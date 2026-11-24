import argparse
from contextlib import ExitStack
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location('lab', Path(__file__).resolve().parents[1] / 'scripts/lab.py')
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(404 if self.path == '/missing' else 200)
        self.end_headers()
        self.wfile.write(b'OK\n' if self.path == '/health' else b'not healthy')

    def log_message(self, *args):
        pass


class HealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_real_http_200_and_fixed_body(self):
        self.assertEqual(lab.health(self.url + '/health')['status'], 200)

    def test_reject_200_with_wrong_body(self):
        with self.assertRaises(RuntimeError):
            lab.health(self.url + '/wrong')

    def test_reject_http_error(self):
        with self.assertRaises(lab.urllib.error.HTTPError):
            lab.health(self.url + '/missing')


class SafetyTests(unittest.TestCase):
    def test_policy_covers_ec2_waiter_read_operations(self):
        from botocore.session import get_session
        root = Path(__file__).resolve().parents[1]
        policy = json.loads((root / 'iam/mission-policy.json').read_text())
        allowed = {action for statement in policy['Statement'] if statement['Effect'] == 'Allow'
                   for action in ([statement['Action']] if isinstance(statement['Action'], str) else statement['Action'])}
        model = get_session().get_waiter_model('ec2')
        for name in ['VpcAvailable', 'InstanceRunning', 'InstanceStatusOk', 'InstanceTerminated', 'VolumeDeleted']:
            with self.subTest(waiter=name):
                self.assertIn('ec2:' + model.get_waiter(name).operation, allowed)

    def test_refuse_root_credentials(self):
        with patch('boto3.Session') as session:
            session.return_value.client.return_value.get_caller_identity.return_value = {'Arn': 'arn:aws:iam::123:root'}
            with self.assertRaisesRegex(RuntimeError, 'Root credentials'):
                lab.clients('example')

    def test_broad_ssh_ranges_rejected_before_aws(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(lab, 'STATE', Path(directory) / 'no-state'), \
             patch.object(lab, 'clients') as clients:
            for cidr in ['0.0.0.0/0', '8.8.8.0/24', '127.0.0.1/32', '::/0']:
                with self.subTest(cidr=cidr), self.assertRaises(ValueError):
                    lab.deploy(argparse.Namespace(ssh_cidr=cidr, free_tier_checked=True))
            clients.assert_not_called()

    def test_free_tier_ack_required_before_aws(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(lab, 'STATE', Path(directory) / 'no-state'), \
             patch.object(lab, 'clients') as clients:
            with self.assertRaisesRegex(ValueError, 'eligibility'):
                lab.deploy(argparse.Namespace(ssh_cidr='8.8.8.8/32', free_tier_checked=False))
            clients.assert_not_called()

    def test_wrong_account_refuses_cleanup_before_api_mutation(self):
        ec2 = Mock()
        with patch.object(lab, 'load', return_value={'account': 'original'}), \
             patch.object(lab, 'clients', return_value=(ec2, {'Account': 'other'})):
            with self.assertRaisesRegex(RuntimeError, 'another AWS account'):
                lab.cleanup(argparse.Namespace(profile='example'))
        self.assertEqual(ec2.mock_calls, [])

    def test_unexpected_ingress_fails_before_ssh(self):
        ec2 = Mock()
        ec2.describe_security_groups.return_value = {'SecurityGroups': [{'IpPermissions': [
            {'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]}]}
        state = {'account': '123', 'sg': 'sg-lab', 'ssh_cidr': '8.8.8.8/32'}
        with patch.object(lab, 'load', return_value=state), \
             patch.object(lab, 'clients', return_value=(ec2, {'Account': '123'})), \
             patch.object(lab, 'ssh') as ssh:
            with self.assertRaisesRegex(RuntimeError, 'Unexpected inbound'):
                lab.verify(argparse.Namespace(profile='example'))
            ssh.assert_not_called()

    def test_failed_diagnosis_still_restarts_service(self):
        calls = []
        def execute(state, command):
            calls.append(command)
            if 'is-active' in command:
                raise RuntimeError('SSH diagnostic interrupted')
            return ''
        state = {'account': '123', 'ip': '192.0.2.10'}
        with patch.object(lab, 'load', return_value=state), \
             patch.object(lab, 'clients', return_value=(Mock(), {'Account': '123'})), \
             patch.object(lab, 'health', side_effect=[{'status': 200}, OSError('connection refused')]), \
             patch.object(lab, 'ssh', side_effect=execute):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                lab.troubleshoot(argparse.Namespace(profile='example'))
        self.assertIn('sudo systemctl start nginx && sudo nginx -t', calls)

    def test_partial_deployment_cleanup_uses_both_tags_and_is_repeatable(self):
        ec2 = Mock()
        responses = {'describe_instances': 'Reservations', 'describe_volumes': 'Volumes',
            'describe_security_groups': 'SecurityGroups', 'describe_route_tables': 'RouteTables',
            'describe_subnets': 'Subnets', 'describe_internet_gateways': 'InternetGateways',
            'describe_vpcs': 'Vpcs', 'describe_key_pairs': 'KeyPairs', 'describe_addresses': 'Addresses'}
        for method, key in responses.items():
            getattr(ec2, method).return_value = {key: []}
        state = {'account': '123', 'run': 'unique-run'}
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            (root / 'docs').mkdir()
            stack.enter_context(patch.object(lab, 'ROOT', root))
            stack.enter_context(patch.object(lab, 'load', return_value=state))
            stack.enter_context(patch.object(lab, 'clients', return_value=(ec2, {'Account': '123'})))
            stack.enter_context(patch.object(lab, 'save'))
            for _ in range(2):
                lab.cleanup(argparse.Namespace(profile='example'))
            report = json.loads((root / 'docs/evidence/cleanup.json').read_text())
            self.assertFalse(any(report['remaining'].values()))
        for call in ec2.mock_calls:
            filters = call.kwargs['Filters']
            self.assertEqual(filters, [
                {'Name': 'tag:Project', 'Values': ['mission_B3-1']},
                {'Name': 'tag:LabRun', 'Values': ['unique-run']}])


if __name__ == '__main__':
    unittest.main()
