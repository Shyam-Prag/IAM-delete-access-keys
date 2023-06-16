lambda_function.py is a Lambda function which scans IAM users within an account and removes access keys which have not been used in > than max_idle_days. 

This can be triggered via an eventBridge CRON job which triggers the function on a CRON schedule. 
