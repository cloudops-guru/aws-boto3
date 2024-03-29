import boto3    
# Intention of this script to find all instances with open ssh access or All traffic enabled
# This will check all secuity group with breaches and check for instance attached  
# A consolidated report will be send over a mail

def lambda_handler(event, context): 
  alertMsg=""
  for region in ["ap-south-1","ap-southeast-1", "us-west-2"]:
    ec2Client=boto3.client('ec2', region )
    SecurityGroups = ec2Client.describe_security_groups()["SecurityGroups"]  
    for sg in SecurityGroups: 
        for rulesRow in sg["IpPermissions"]: 
          alertMsg+=iterateFetchBreach(rulesRow,ec2Client,sg,region) 
          
  #This condiction checks for security breaches are there or not 
  if (len(alertMsg) > 0):
    sendSNSAlert(boto3,alertMsg)
     
                      
def iterateFetchBreach(rulesRow,ec2Client,sg,region):
  #Following line checks for ssh access or ALL traffic enabled
  if ( ('FromPort' in rulesRow and rulesRow['FromPort'] == 22 ) or ('IpProtocol' in rulesRow and rulesRow['IpProtocol'] == '-1' )) :
    
    for cidr in rulesRow["IpRanges"]: 
      if cidr['CidrIp']=="0.0.0.0/0":  
        sgid=sg["GroupId"]  
        #Filter with security group and server status
        ec2_instance = ec2Client.describe_instances(Filters=[{
        'Name': 'network-interface.group-id',
        'Values': [sgid]
        },{
        'Name': 'instance-state-name',
        'Values': ['running']
        }]) 
        for instances in ec2_instance['Reservations']:
          for instance in instances['Instances']:
            return "Instance ID:" + instance['InstanceId'] + " Security Group: " + sgid+"\n"
  return ""  
          
#FUNCTION to SEND SNS Notification          
def sendSNSAlert(boto3,alertMsg):
  sns = boto3.client('sns')
  print("Security Breach Alert (Port 22 Open in instances): \n" + alertMsg)
  response = sns.publish(
      #Dont put the numbers coming after the topic name in the ARN
      TopicArn='arn:aws:sns:region:accountnumber:SNSTipicName',    
      Message="Security Breach Alert (Port 22 Open in instances): \n" +alertMsg,    
     )