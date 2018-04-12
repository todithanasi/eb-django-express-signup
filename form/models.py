import time
from django.db import models
import boto3
import os
import logging
import time
from dateutil import parser

STARTUP_SIGNUP_TABLE = os.environ['STARTUP_SIGNUP_TABLE']
AWS_REGION = os.environ['AWS_REGION']
NEW_SIGNUP_TOPIC = os.environ['NEW_SIGNUP_TOPIC']

logger = logging.getLogger(__name__)


class Leads(models.Model):

    def insert_lead(self, name, email, previewAccess):
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(STARTUP_SIGNUP_TABLE)
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        try:
            response = table.put_item(
                Item={
                    'name': name,
                    'email': email,
                    'preview': previewAccess,
                },
                ReturnValues='ALL_OLD',
            )
        except Exception as e:
            logger.error(
                'Error adding item to database: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return 403
        status = response['ResponseMetadata']['HTTPStatusCode']
        if status == 200:
            if 'Attributes' in response:
                logger.error('Existing item updated to database.')
                return 409
            logger.error('New item added to database.')
        else:
            logger.error('Unknown error inserting item to database.')

        return status

    def send_notification(self, email):
        sns = boto3.client('sns', region_name=AWS_REGION)
        try:
            sns.publish(
                TopicArn=NEW_SIGNUP_TOPIC,
                Message='New signup: %s' % email,
                Subject='New signup',
            )
            logger.error('SNS message sent.')

        except Exception as e:
            logger.error(
                'Error sending SNS message: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))




    def get_leads(self, domain, preview):
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table('gsg-signup-table')
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return None
        expression_attribute_values = {}
        FilterExpression = []
        if preview:
            expression_attribute_values[':p'] = preview
            FilterExpression.append('preview = :p')
        if domain:
            expression_attribute_values[':d'] = '@' + domain
            FilterExpression.append('contains(email, :d)')
        if expression_attribute_values and FilterExpression:
            response = table.scan(
                FilterExpression=' and '.join(FilterExpression),
                ExpressionAttributeValues=expression_attribute_values,
            )
        else:
            response = table.scan(
                AttributesToGet=['email'],
                ReturnConsumedCapacity='TOTAL',
            )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return response['Items']
        logger.error('Unknown error retrieving items from database.')
        return None

class Tweets(models.Model):

    def get_tweets(self, from_date, to_date):
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table('twitter-geo')
        except Exception as e:
            logger.error(
                'Error connecting to database table: ' + (e.fmt if hasattr(e, 'fmt') else '') + ','.join(e.args))
            return None
        expression_attribute_values = {}
        FilterExpression = []
        if from_date:
            from_date_parsed_init = time.strptime(from_date, '%Y-%m-%d-%H-%M')
            str_from_date = time.strftime('%Y-%m-%d %H:%M', from_date_parsed_init)
            from_date_parsed = str(parser.parse(str_from_date).timestamp())
            expression_attribute_values[':fd'] = from_date_parsed
            FilterExpression.append('created_at >= :fd')
        if to_date:
            to_date_parsed_init = time.strptime(to_date, '%Y-%m-%d-%H-%M')
            str_to_date = time.strftime('%Y-%m-%d %H:%M', to_date_parsed_init)
            to_date_parsed = str(parser.parse(str_to_date).timestamp())
            expression_attribute_values[':td'] = to_date_parsed
            FilterExpression.append('created_at < :td')
        if expression_attribute_values and FilterExpression:
            response = table.scan(
                FilterExpression=' and '.join(FilterExpression),
                ExpressionAttributeValues=expression_attribute_values,
            )
        else:
            response = table.scan(
                ReturnConsumedCapacity='TOTAL',
            )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return response['Items']
        logger.error('Unknown error retrieving items from database.')
        return None

