#!/usr/bin/env python3
"""
Restart the application on the existing AWS instance
"""
import boto3
import time

def restart_application():
    print("🔄 Restarting RichesReach application on AWS...")
    
    # Initialize AWS client
    ec2 = boto3.client('ec2', region_name='us-east-2')
    ssm = boto3.client('ssm', region_name='us-east-2')
    
    try:
        # Get the existing instance
        response = ec2.describe_instances(
            InstanceIds=['i-0cf93dd9f7f54ce93']
        )
        
        instance = response['Reservations'][0]['Instances'][0]
        public_ip = instance['PublicIpAddress']
        state = instance['State']['Name']
        
        print(f"🖥️  Instance Status: {state}")
        print(f"🌐 Public IP: {public_ip}")
        
        if state != 'running':
            print("❌ Instance is not running")
            return False
        
        # Use AWS Systems Manager to run commands on the instance
        print("🔧 Restarting application via AWS Systems Manager...")
        
        # Commands to restart the application
        restart_commands = [
            "sudo systemctl stop richesreach || true",
            "sudo docker stop $(sudo docker ps -q) || true",
            "sudo docker rm $(sudo docker ps -aq) || true",
            "cd /tmp && sudo rm -rf richesreach-ai.zip || true",
            "sudo pkill -f 'python.*main:app' || true",
            "sudo pkill -f 'uvicorn' || true",
            "sleep 5",
            "cd /tmp && sudo python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/richesreach.log 2>&1 &",
            "sleep 10",
            "curl -f http://localhost:8000/health || echo 'Health check failed'"
        ]
        
        for i, command in enumerate(restart_commands, 1):
            print(f"📋 Step {i}/{len(restart_commands)}: {command}")
            
            try:
                response = ssm.send_command(
                    InstanceIds=['i-0cf93dd9f7f54ce93'],
                    DocumentName='AWS-RunShellScript',
                    Parameters={'commands': [command]},
                    TimeoutSeconds=60
                )
                
                command_id = response['Command']['CommandId']
                
                # Wait for command to complete
                time.sleep(5)
                
                # Get command output
                output = ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId='i-0cf93dd9f7f54ce93'
                )
                
                if output['Status'] == 'Success':
                    print(f"✅ Step {i} completed")
                else:
                    print(f"⚠️  Step {i} had issues: {output.get('StandardErrorContent', 'No error details')}")
                
            except Exception as e:
                print(f"⚠️  Step {i} failed: {e}")
                continue
        
        print("🎉 Application restart completed!")
        print(f"🌐 Your app should be available at: http://{public_ip}:8000")
        print(f"🏥 Health check: http://{public_ip}:8000/health")
        
        return True
        
    except Exception as e:
        print(f"❌ Restart failed: {e}")
        return False

if __name__ == "__main__":
    restart_application()
