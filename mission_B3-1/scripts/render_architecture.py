"""Render the deployed lab diagram; run after deploy. Requires Pillow."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
state=json.loads((ROOT/'.local/state.json').read_text())
canvas=Image.new('RGB',(1600,1080),'#f3f7fc')
draw=ImageDraw.Draw(canvas)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
if not Path(fontpath).exists(): fontpath='DejaVuSans.ttf'
def text(x,y,value,size=24,color='#172b47'):
    draw.text((x,y),value,font=ImageFont.truetype(fontpath,size),fill=color)
def box(rect,title,lines,fill='white'):
    draw.rounded_rectangle(rect,radius=18,fill=fill,outline='#7793b8',width=3)
    x,y=rect[:2];text(x+20,y+16,title,28)
    for i,line in enumerate(lines):text(x+20,y+58+i*32,line,22)
def arrow(points,color='#2463d1'):
    draw.line(points,fill=color,width=5)
    (x0,y0),(x,y)=points[-2:]
    if x0==x:
        delta=1 if y>y0 else -1
        tri=[(x,y),(x-10,y-16*delta),(x+10,y-16*delta)]
    else:
        delta=1 if x>x0 else -1
        tri=[(x,y),(x-16*delta,y-10),(x-16*delta,y+10)]
    draw.polygon(tri,fill=color)
text(45,25,'MISSION B3-1 | Deployed AWS architecture',40)
text(45,80,'Seoul ap-northeast-2 | Run '+state['run']+' | Resources deleted after evidence collection',24)
box((480,140,1555,875),'VPC 10.30.0.0/16',[state['vpc']],fill='#e7effc')
box((570,440,1470,810),'Public Subnet 10.30.1.0/24',[state['subnet']],fill='#effaf4')
box((610,255,1090,405),'Internet Gateway',[state['igw'],'Attached to lab VPC'])
box((1130,255,1505,405),'Route Table',['0.0.0.0/0 -> IGW','Associated with lab subnet'])
box((650,565,1390,755),'Security Group + EC2 / Nginx',[
    'SG: HTTP 80 any IPv4 | SSH 22 operator /32',
    state['instance']+' | t3.micro | Amazon Linux 2023',
    'Public IPv4: '+state.get('ip','pending')+' | /health -> HTTP 200 OK',
    'Encrypted EBS gp3 8 GiB | delete on termination'])
box((45,200,415,345),'Internet clients',['HTTP :80','Existing mission_B1-1 website'])
box((45,440,415,585),'Operator workstation',['SSH :22 from '+state['ssh_cidr'],'Locally generated Ed25519 key'])
arrow([(415,275),(610,275)])
arrow([(850,405),(850,425),(1440,425),(1440,650),(1390,650)])
arrow([(415,520),(510,520),(510,785),(1000,785),(1000,755)],'#15916a')
arrow([(1390,700),(1530,700),(1530,420),(1330,420),(1330,405)],'#8159b5')
text(620,840,'Blue: HTTP ingress | Green: SSH | Purple: return / outbound',23)
box((45,920,940,1050),'IAM authorization',['Dedicated mission-b3 user; no AdministratorAccess','EC2 / VPC / SG actions limited to Seoul; no credentials on EC2'])
box((980,920,1555,1050),'Lifecycle',['Deploy -> verify -> incident recovery -> cleanup','No EIP / NAT Gateway / ALB / RDS created'])
canvas.save(ROOT/'docs/architecture.png')
