# src/lambda_worker/dynamodb_utils.py
import os
import boto3

DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)
