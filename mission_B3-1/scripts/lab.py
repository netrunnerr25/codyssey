#!/usr/bin/env python3
"""AWS Seoul lab. Credentials use boto3's normal profile/SSO chain; never saved here."""
import argparse
import datetime as dt
import ipaddress
import json
from pathlib import Path
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local'
STATE = PRIVATE / 'state.json'
REGION = 'ap-northeast-2'
PROJECT = 'mission_B3-1'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(state):
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.chmod(0o600)
    tmp.replace(STATE)


def load():
    return json.loads(STATE.read_text())


def tags(state):
    return [{'Key': 'Project', 'Value': PROJECT},
            {'Key': 'LabRun', 'Value': state['run']},
            {'Key': 'Name', 'Value': PROJECT + '-' + state['run']}]


def spec(state, kind):
    return [{'ResourceType': kind, 'Tags': tags(state)}]


def clients(profile):
    import boto3
    session = boto3.Session(profile_name=profile, region_name=REGION)
    identity = session.client('sts').get_caller_identity()
    if identity['Arn'].endswith(':root'):
        raise RuntimeError('Root credentials are forbidden. Use a dedicated IAM user/role.')
    return session.client('ec2'), identity


def same_account(state, identity):
    if state['account'] != identity['Account']:
        raise RuntimeError('State belongs to another AWS account; refusing mutation.')


def cmd(argv):
    result = subprocess.run(argv, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed ({result.returncode}): {result.stderr[-3000:]}')
    return result.stdout


def ssh(state, command):
    return cmd(['ssh', '-i', str(PRIVATE / 'ssh-key'), '-o', 'BatchMode=yes',
                '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=accept-new',
                '-o', 'UserKnownHostsFile=' + str(PRIVATE / 'known_hosts'),
                'ec2-user@' + state['ip'], command])


def health(url, timeout=10):
    # Disable proxy variables: evidence must come from this public endpoint.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=timeout) as response:
        body = response.read(4096).decode()
        if response.status != 200 or body != 'OK\n':
            raise RuntimeError(f'Unexpected health response: {response.status}, {body!r}')
        return {'url': url, 'status': response.status, 'body': body, 'checked_at': now()}


def retry(fn, attempts=40, pause=10):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i + 1 == attempts:
                raise
            time.sleep(pause)


def deploy(args):
    if STATE.exists():
        raise RuntimeError('Existing state found. Verify/cleanup that run before starting another.')
    # Require an explicit single IPv4 address; never broaden SSH access automatically.
    network = ipaddress.ip_network(args.ssh_cidr, strict=True)
    if network.version != 4 or network.prefixlen != 32 or not network.network_address.is_global:
        raise ValueError('--ssh-cidr must be your public IPv4 address followed by /32')
    if not args.free_tier_checked:
        raise ValueError('Confirm account eligibility/remaining credits, then pass --free-tier-checked')
    website = Path(args.website).resolve()
    if not (website / 'index.html').is_file():
        raise ValueError('Existing website directory must contain index.html')
    ec2, identity = clients(args.profile)
    images = ec2.describe_images(Owners=['amazon'], Filters=[
        {'Name': 'name', 'Values': ['al2023-ami-2023.*-x86_64']},
        {'Name': 'state', 'Values': ['available']},
        {'Name': 'architecture', 'Values': ['x86_64']},
        {'Name': 'root-device-type', 'Values': ['ebs']}])['Images']
    image = max(images, key=lambda x: x['CreationDate'])
    eligible = ec2.describe_instance_types(InstanceTypes=['t3.micro'])['InstanceTypes'][0]
    if not eligible.get('FreeTierEligible'):
        raise RuntimeError('t3.micro is not marked FreeTierEligible by AWS in this region')
    state = {'run': uuid.uuid4().hex[:12], 'account': identity['Account'],
             'caller_arn': identity['Arn'], 'region': REGION, 'ssh_cidr': str(network),
             'started_at': now(), 'ami': image['ImageId'], 'stage': 'creating'}
    save(state)
    # Persist each ID immediately so partial deployments can be cleaned up.
    def remember(key, value):
        state[key] = value
        save(state)
        return value
    try:
        vpc = remember('vpc', ec2.create_vpc(CidrBlock='10.30.0.0/16',
                       TagSpecifications=spec(state, 'vpc'))['Vpc']['VpcId'])
        ec2.get_waiter('vpc_available').wait(VpcIds=[vpc])
        subnet = remember('subnet', ec2.create_subnet(VpcId=vpc, CidrBlock='10.30.1.0/24',
                          TagSpecifications=spec(state, 'subnet'))['Subnet']['SubnetId'])
        igw = remember('igw', ec2.create_internet_gateway(
                       TagSpecifications=spec(state, 'internet-gateway'))['InternetGateway']['InternetGatewayId'])
        ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc)
        route = remember('route_table', ec2.create_route_table(VpcId=vpc,
                         TagSpecifications=spec(state, 'route-table'))['RouteTable']['RouteTableId'])
        ec2.create_route(RouteTableId=route, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw)
        remember('association', ec2.associate_route_table(RouteTableId=route, SubnetId=subnet)['AssociationId'])
        sg = remember('sg', ec2.create_security_group(GroupName=PROJECT + '-' + state['run'],
                      Description='HTTP public; SSH single operator IP', VpcId=vpc,
                      TagSpecifications=spec(state, 'security-group'))['GroupId'])
        ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
             'IpRanges': [{'CidrIp': str(network)}]}])
        # Retain AWS default outbound access for updates, DNS and the required curl test.
        cmd(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(PRIVATE / 'ssh-key')])
        keyname = PROJECT + '-' + state['run']
        remember('keypair', keyname)
        ec2.import_key_pair(KeyName=keyname, PublicKeyMaterial=(PRIVATE / 'ssh-key.pub').read_bytes(),
                            TagSpecifications=spec(state, 'key-pair'))
        instance = ec2.run_instances(ImageId=image['ImageId'], InstanceType='t3.micro',
            MinCount=1, MaxCount=1, KeyName=keyname, ClientToken=state['run'],
            NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': subnet, 'Groups': [sg],
                                'AssociatePublicIpAddress': True, 'DeleteOnTermination': True}],
            BlockDeviceMappings=[{'DeviceName': image['RootDeviceName'], 'Ebs': {
                'VolumeSize': 8, 'VolumeType': 'gp3', 'Encrypted': True, 'DeleteOnTermination': True}}],
            MetadataOptions={'HttpTokens': 'required', 'HttpEndpoint': 'enabled'},
            CreditSpecification={'CpuCredits': 'standard'},
            UserData=(ROOT / 'scripts/user-data.sh').read_text(),
            TagSpecifications=spec(state, 'instance') + spec(state, 'volume') + spec(state, 'network-interface')
        )['Instances'][0]
        remember('instance', instance['InstanceId'])
        ec2.get_waiter('instance_running').wait(InstanceIds=[state['instance']])
        ec2.get_waiter('instance_status_ok').wait(InstanceIds=[state['instance']])
        current = ec2.describe_instances(InstanceIds=[state['instance']])['Reservations'][0]['Instances'][0]
        remember('volumes', [x['Ebs']['VolumeId'] for x in current['BlockDeviceMappings']])
        remember('ip', current['PublicIpAddress'])
        retry(lambda: ssh(state, 'cloud-init status --wait && sudo nginx -t'), attempts=30)
        archive = PRIVATE / 'website.tar.gz'
        # Only web assets; omit dotfiles, credentials, logs, and previous screenshots.
        with tarfile.open(archive, 'w:gz') as tar:
            for p in website.rglob('*'):
                relative = p.relative_to(website)
                if p.is_file() and not p.is_symlink() and not any(x.startswith('.') for x in relative.parts) \
                   and p.suffix.lower() in {'.html', '.css', '.js', '.jpg', '.jpeg', '.png', '.svg', '.ico', '.webp', '.woff', '.woff2'} \
                   and 'screenshots' not in relative.parts:
                    tar.add(p, arcname=str(relative))
        cmd(['scp', '-i', str(PRIVATE / 'ssh-key'), '-o', 'BatchMode=yes',
             '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(PRIVATE / 'known_hosts'),
             str(archive), 'ec2-user@' + state['ip'] + ':/tmp/mission-website.tar.gz'])
        ssh(state, 'sudo tar -xzf /tmp/mission-website.tar.gz -C /usr/share/nginx/html '
                   '&& sudo chmod -R a+rX /usr/share/nginx/html && rm /tmp/mission-website.tar.gz')
        state['stage'] = 'deployed'
        save(state)
        print('Deployed:', 'http://' + state['ip'], '\nNext: verify, troubleshoot, cleanup')
    except Exception:
        print('Partial deployment state saved. Run cleanup using the same AWS profile.')
        raise


def evidence_dir():
    path = ROOT / 'docs/evidence'
    path.mkdir(exist_ok=True)
    return path


def verify(args):
    state = load()
    ec2, identity = clients(args.profile)
    same_account(state, identity)
    sg = ec2.describe_security_groups(GroupIds=[state['sg']])['SecurityGroups'][0]
    expected = {(80, 80, '0.0.0.0/0'), (22, 22, state['ssh_cidr'])}
    actual = set()
    for rule in sg['IpPermissions']:
        if rule['IpProtocol'] != 'tcp' or rule.get('Ipv6Ranges') or rule.get('UserIdGroupPairs') or rule.get('PrefixListIds'):
            raise RuntimeError('Unexpected inbound rule')
        actual.update((rule['FromPort'], rule['ToPort'], r['CidrIp']) for r in rule['IpRanges'])
    if actual != expected:
        raise RuntimeError(f'Unexpected ingress: {actual!r}')
    routes = ec2.describe_route_tables(RouteTableIds=[state['route_table']])['RouteTables'][0]
    assert any(r.get('DestinationCidrBlock') == '0.0.0.0/0' and r.get('GatewayId') == state['igw']
               and r['State'] == 'active' for r in routes['Routes']), 'Missing active Internet route'
    output = ssh(state, "set -eu; systemctl is-active nginx; sudo nginx -t; "
                 "test \"$(curl -sS -o /tmp/local-body -w '%{http_code}' http://localhost)\" = 200; "
                 "curl -fsS http://localhost/health; curl -fsSI --max-time 15 https://example.com; "
                 "sudo tail -n 5 /var/log/nginx/access.log")
    result = retry(lambda: health('http://' + state['ip'] + '/health'))
    result.update({'region': REGION, 'ssh_cidr': state['ssh_cidr'], 'sg_inbound': sg['IpPermissions'],
                   'routes': routes, 'ssh_checks': output})
    path = evidence_dir()
    (path / 'verification.json').write_text(json.dumps(result, indent=2, default=str) + '\n')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1200, 'height': 800})
        response = page.goto(result['url'], wait_until='load', timeout=20000)
        if response.status != 200 or page.locator('body').inner_text().strip() != 'OK':
            raise RuntimeError('Browser health verification failed')
        page.screenshot(path=str(path / 'external-health.png'), full_page=True)
        homepage = page.goto('http://' + state['ip'] + '/', wait_until='networkidle', timeout=20000)
        if homepage.status != 200:
            raise RuntimeError('Deployed website did not return HTTP 200')
        page.screenshot(path=str(path / 'external-website.png'), full_page=True)
        browser.close()
    readme = ROOT / 'README.md'
    text = readme.read_text()
    start, end = '<!-- live-result:start -->', '<!-- live-result:end -->'
    replacement = f"\n검증 방식: **B — GET /health**\n\nURL: `{result['url']}`\n\n검증 시각(UTC): `{result['checked_at']}`\n\nHTTP **200**, 응답 `OK` 확인. [실제 브라우저 캡처](docs/evidence/external-health.png), [검증 로그](docs/evidence/verification.json).\n\n실습 종료 후 cleanup을 실행하면 해당 URL은 더 이상 서비스하지 않습니다.\n"
    a, b = text.index(start) + len(start), text.index(end)
    readme.write_text(text[:a] + replacement + text[b:])
    print('Verified external 200 OK; browser screenshot and SSH/network evidence saved.')


def troubleshoot(args):
    state = load()
    ec2, identity = clients(args.profile)
    same_account(state, identity)
    url = 'http://' + state['ip'] + '/health'
    before = health(url)
    # Real controlled service outage; SG and SSH access remain intact.
    log = {'before': before, 'started_at': now()}
    try:
        ssh(state, 'sudo systemctl stop nginx')
        log['service_stopped'] = True
        try:
            health(url, timeout=5)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            log['observed_failure'] = str(error)
        else:
            raise RuntimeError('Expected external connection failure was not reproduced')
        log['diagnosis'] = ssh(state, "systemctl is-active nginx || true; sudo ss -lntp; "
                               "sudo journalctl -u nginx -n 12 --no-pager")
    finally:
        ssh(state, 'sudo systemctl start nginx && sudo nginx -t')
    log['after'] = retry(lambda: health(url), attempts=10, pause=3)
    path = evidence_dir()
    (path / 'troubleshooting.json').write_text(json.dumps(log, indent=2) + '\n')
    (ROOT / 'docs/troubleshooting.md').write_text(f'''# 트러블슈팅 보고서

실제 AWS 인스턴스에서 의도적으로 Nginx를 중지해 재현한 장애입니다.

| 항목 | 실제 관찰/조치 |
|---|---|
| 증상 | 정상 응답하던 `{url}`에서 접속 실패 |
| 가설 | 웹 서버 프로세스가 중지되어 80 포트에서 수신하지 않음 |
| 검증 | SSH 유지 상태에서 `systemctl is-active nginx`, `ss -lntp`, `journalctl -u nginx` 확인 |
| 조치 | `sudo systemctl start nginx`, `sudo nginx -t` |
| 결과 | 복구 후 외부 GET /health HTTP {log['after']['status']}, OK |
| 재발방지 | systemctl enable 설정, 배포 후 로컬/외부 헬스체크, 장애 재현 코드는 finally에서 서비스 복구 |

실행 시각(UTC): {log['started_at']}

가공 전 실제 진단 출력과 전후 HTTP 응답: [troubleshooting.json](evidence/troubleshooting.json).
''')
    print('Actual outage reproduced, diagnosed, and recovered; evidence saved.')


def cleanup(args):
    from botocore.exceptions import ClientError
    state = load()
    ec2, identity = clients(args.profile)
    same_account(state, identity)
    filters = [{'Name': 'tag:Project', 'Values': [PROJECT]},
               {'Name': 'tag:LabRun', 'Values': [state['run']]}]
    report = {'run': state['run'], 'started_at': now(), 'actions': []}
    def action(name, **kwargs):
        try:
            getattr(ec2, name)(**kwargs)
        except ClientError as e:
            if not e.response['Error']['Code'].endswith('.NotFound'):
                raise
        report['actions'].append(name)
    # Discover by both run tags, including resources created just before a state-write failure.
    reservations = ec2.describe_instances(Filters=filters)['Reservations']
    instances = [i for r in reservations for i in r['Instances']]
    volumes = {x['VolumeId'] for x in ec2.describe_volumes(Filters=filters)['Volumes']}
    volumes.update(state.get('volumes', []))
    ids = [i['InstanceId'] for i in instances if i['State']['Name'] != 'terminated']
    if ids:
        action('terminate_instances', InstanceIds=ids)
        ec2.get_waiter('instance_terminated').wait(InstanceIds=ids)
    for volume in volumes:
        retry(lambda: action('delete_volume', VolumeId=volume), attempts=20, pause=5)
        ec2.get_waiter('volume_deleted').wait(VolumeIds=[volume])
    for sg in ec2.describe_security_groups(Filters=filters)['SecurityGroups']:
        retry(lambda: action('delete_security_group', GroupId=sg['GroupId']), attempts=20, pause=5)
    for rt in ec2.describe_route_tables(Filters=filters)['RouteTables']:
        for association in rt['Associations']:
            if not association.get('Main'):
                action('disassociate_route_table', AssociationId=association['RouteTableAssociationId'])
        action('delete_route_table', RouteTableId=rt['RouteTableId'])
    for subnet in ec2.describe_subnets(Filters=filters)['Subnets']:
        action('delete_subnet', SubnetId=subnet['SubnetId'])
    for igw in ec2.describe_internet_gateways(Filters=filters)['InternetGateways']:
        for attachment in igw['Attachments']:
            action('detach_internet_gateway', InternetGatewayId=igw['InternetGatewayId'], VpcId=attachment['VpcId'])
        action('delete_internet_gateway', InternetGatewayId=igw['InternetGatewayId'])
    for vpc in ec2.describe_vpcs(Filters=filters)['Vpcs']:
        action('delete_vpc', VpcId=vpc['VpcId'])
    for key in ec2.describe_key_pairs(Filters=filters)['KeyPairs']:
        action('delete_key_pair', KeyName=key['KeyName'])
    checks = {
        'EC2': [i['InstanceId'] for r in ec2.describe_instances(Filters=filters)['Reservations']
                for i in r['Instances'] if i['State']['Name'] != 'terminated'],
        'EBS': ec2.describe_volumes(Filters=filters)['Volumes'],
        'Elastic IP': ec2.describe_addresses(Filters=filters)['Addresses'],
        'Internet Gateway': ec2.describe_internet_gateways(Filters=filters)['InternetGateways'],
        'VPC': ec2.describe_vpcs(Filters=filters)['Vpcs'],
        'Subnet': ec2.describe_subnets(Filters=filters)['Subnets'],
        'Route Table': ec2.describe_route_tables(Filters=filters)['RouteTables'],
        'Security Group': ec2.describe_security_groups(Filters=filters)['SecurityGroups'],
        'Key Pair': ec2.describe_key_pairs(Filters=filters)['KeyPairs']}
    report.update({'finished_at': now(), 'remaining': checks})
    (evidence_dir() / 'cleanup.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
    if any(checks.values()):
        raise RuntimeError('Resources remain. Inspect cleanup.json and rerun cleanup.')
    (ROOT / 'docs/cleanup-checklist.md').write_text('# 리소스 정리 체크리스트\n\n'
        + f"검증 시각(UTC): {report['finished_at']}\n\n"
        + '\n'.join('- [x] ' + name + ': 해당 실습 태그의 잔존 리소스 0개' for name in checks)
        + '\n\n- [x] NAT Gateway, ELB/ALB, RDS: 이 자동화에서 생성하지 않음\n'
        + '- [ ] Billing Dashboard: 계정 소유자가 지연 반영되는 사용 내역/크레딧을 최종 확인\n\n'
        + '근거: [실제 삭제 API 실행 및 재조회 결과](evidence/cleanup.json). '
        + '범위는 Project 및 LabRun 태그가 모두 일치하는 이번 실습 리소스입니다.\n')
    state['stage'] = 'cleaned'
    save(state)
    print('Cleanup verified. Keep state/evidence; check Billing Dashboard separately.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', help='Existing AWS profile/SSO profile')
    sub = parser.add_subparsers(dest='command', required=True)
    deploy_parser = sub.add_parser('deploy')
    deploy_parser.add_argument('--ssh-cidr', required=True)
    deploy_parser.add_argument('--website', default=str(ROOT.parent / 'mission_B1-1'))
    deploy_parser.add_argument('--free-tier-checked', action='store_true')
    for name in ['verify', 'troubleshoot', 'cleanup']:
        sub.add_parser(name)
    args = parser.parse_args()
    globals()[args.command](args)


if __name__ == '__main__':
    main()
