
import boto3
import json
import os

print('Loading function')
dynamo = boto3.client('dynamodb')



def start_or_stop_server(action):

    client = boto3.client('ec2')

    if action == "start_server":
        response = client.start_instances(
            InstanceIds=[
                os.environ['ec2_server_arn'],
            ]
            # AdditionalInfo='string',
            # DryRun=True|False
        )
    elif action == "stop_server":
        response = client.stop_instances(
            InstanceIds=[
                os.environ['ec2_server_arn'],
            ]
            # AdditionalInfo='string',
            # DryRun=True|False
        )
    else:
        print("Invalid parameter in start_or_stop_server()")
        exit()




def get_status():

    instance_status = "Not yet checked"
    client = boto3.client('ec2')
    status_response = client.describe_instances(
    # Filters=[
    #     {
    #         'Name': 'string',
    #         'Values': [
    #             'string',
    #         ]
    #     },
    # ],
    InstanceIds=[
        os.environ['ec2_server_arn'],
    ],
    # MaxResults=10,
    # NextToken='string',
    # DryRun=True|False,
    )

    # print("status_response={}".format(status_response))

    for reservation in status_response['Reservations']:
        for instance in reservation['Instances']:
            if instance['InstanceId'] == os.environ['ec2_server_arn']:
                instance_status = instance['State']['Name']

    return instance_status






def server_action(actionType):

    sns_message = "Initialized"

    if actionType == "start_server":
        start_or_stop_server("start_server")
        sns_message = "Requesting server start for:   owncloud.adrianws.com "


    if actionType == "get_status":

        server_status = "?"
        server_status = get_status()

        sns_message = "The status for  owncloud.adrianws.com  is:  {}".format(server_status)


    if actionType == "stop_server":
        start_or_stop_server("stop_server")
        sns_message = "Requesting server stop for:   owncloud.adrianws.com "




    #Publish command_result to SNS topic   
    client = boto3.client('sns')

    publish_response = client.publish(
        TopicArn=os.environ['sns_topic_arn'],
        Message=sns_message,
        Subject='StartEC2andRedirect: server_action() message',
    )







def respond(err, res=None):
    # print(err)

    #http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-set-up-simple-proxy.html#api-gateway-simple-proxy-for-lambda-output-format
    # proper_response = {{
    # "isBase64Encoded": true|false,
    # "statusCode": httpStatusCode,
    # "headers": { "headerName": "headerValue", ... },
    # "body": "..."
    # }
    return_data = {
        "isBase64Encoded": False,
        'statusCode': '400' if err else '302',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
            'Location': os.environ['redirect_to_url'],
        },
    }

    return return_data


def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.'''



    print("Received event: " + json.dumps(event, indent=2))

    # httpMethod = event['httpMethod']
    queryStringParameters = event['queryStringParameters'] 
    operation = event['httpMethod']
    # operation = event['input']['httpMethod']


    if operation == 'PUT':
        print("Received PUT event")
        command_result = server_action("start_server")
        return respond(None,"Thank you")

    elif operation == 'GET':
        print("Received GET event")
        command_result = server_action("get_status")
        return respond(None,"Thank you")
    
    elif operation == 'POST':
        print("Received POST event")
        command_result = server_action("stop_server")
        return respond(None,"Thank you")

    else:
        error_message = "ERROR: Received Non-Supported event in Lambda function"
        print(error_message)
        return respond('BAD REQUEST', error_message)







