import json
import boto3
from datetime import datetime
from datetime import timedelta
from botocore.exceptions import ClientError

list_access_keys_to_remove = []
date_now = datetime.now()
iam_client = boto3.client('iam')
max_idle_days = 30
max_items = 50

def lambda_handler(event, context):

    try:
        res_users = iam_client.list_users(
            MaxItems=max_items
        )
        print(res_users)
        check_credentials(res_users)
    except ClientError as error:
        print('An error occurred while fetching user list.', error)
        return

    if res_users['IsTruncated']:
        while res_users['IsTruncated']:
            marker = res_users['Marker']
            try:
                res_users = iam_client.list_users(
                    Marker=marker,
                    MaxItems=max_items
                )

                check_credentials(res_users)
            except ClientError as error:
                print('An error occurred while fetching user list.', error)
                return


    for access_key_id in list_access_keys_to_remove:
        print('Access key {0} needs to be made inactive'.format(access_key_id))
    
    return list_access_keys_to_remove


def check_credentials(res_users):
    created_date = datetime.now()
    last_used_date = datetime.now()
    access_key_id = None

    for user in res_users['Users']:
        if 'PasswordLastUsed' in user: # Checking for console user password last usage
            last_used_date = user['PasswordLastUsed'].replace(tzinfo=None)

            difference = date_now - last_used_date

            if difference.days > max_idle_days:
                print('PSST...there are some users that need to be removed')
        
        
        # Below we are checking for access keys last usage
        try:
            res_keys = iam_client.list_access_keys(
                UserName=user['UserName'],
                MaxItems=2)
               

            if 'AccessKeyMetadata' in res_keys:
                for key in res_keys['AccessKeyMetadata']:
                    
                    if 'CreateDate' in key:
                        created_date = res_keys['AccessKeyMetadata'][0]['CreateDate'].replace(tzinfo=None)
                        
                    if 'AccessKeyId' and 'UserName'in key:
                        access_key_id = key['AccessKeyId']
                        attachedUserName = key['UserName']
                       # userNameUserName = res_keys['AccessKeyMetadata'][0]['UserName']
                        
                        res_last_used_key = iam_client.get_access_key_last_used(
                            AccessKeyId=access_key_id)
                        if 'LastUsedDate' in key:
                            last_used_date = res_last_used_key['AccessKeyLastUsed']['LastUsedDate'].replace(tzinfo=None)
                            
                        else:
                            last_used_date = created_date
                        difference = date_now - last_used_date
                
                        if difference.days > max_idle_days:
                            to_be_removed = {
                                'key': access_key_id,
                                'userName': attachedUserName
                            }
                            list_access_keys_to_remove.append(to_be_removed)
                
                            response = iam_client.delete_access_key(
                            UserName = to_be_removed['userName'] ,
                            AccessKeyId= to_be_removed['key'] 
                            )
        except ClientError as error:
            print('An error occurred while listing access keys', error)
            return