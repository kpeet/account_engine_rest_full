from django.conf import settings


def generate_sns_topic(sns_topic_name):
    sns_topic = '-'.join([settings.SNS_COUNTRY_PREFIX, settings.SNS_ENV_PREFIX, sns_topic_name])
    return sns_topic
