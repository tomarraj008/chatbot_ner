import boto
import boto3
from chatbot_ner.config import ner_logger
from lib.singleton import Singleton
from lib.utils import get_cache_ml


def read_model_dict_from_s3(bucket_name, bucket_region, model_path_location=None):
    """
    Read model dict from s3 for given model path location
    :param bucket_name: s3 bucket name
    :param model_path_location: model path location for domain
    :return:
    """
    model_dict = None
    try:
        s3 = boto3.resource('s3', region_name=bucket_region)
        bucket = s3.Bucket(bucket_name)
        pickle_file_handle = bucket.Object(model_path_location.lstrip('/'))
        # note read() will return str and hence cPickle.loads
        model_dict = pickle_file_handle.get()['Body'].read()
        ner_logger.debug("Model Read Successfully From s3")
    except Exception as e:
        ner_logger.exception("Error Reading model from s3 for domain %s " % e)
    return model_dict


def write_file_to_s3(bucket_name, address, disk_filepath, bucket_region=None):
    """
    Upload file on disk to s3 bucket with the given address
    WARNING! File will be overwritten if it exists

    Args:
        bucket_name (str): name of the bucket to upload file to
        address (str): full path including filename inside the bucket to upload the file at
        disk_filepath (str): full path including filename on disk of the file to upload to s3 bucket
        bucket_region (str, Optional): region of the s3 bucket, defaults to None

    Returns:
        bool: indicating whether file upload was successful

    """
    try:
        connection, bucket = get_s3_connection_and_bucket(bucket_name=bucket_name,
                                                          bucket_region=bucket_region)
        key = bucket.new_key(address)
        key.set_contents_from_filename(disk_filepath)
        connection.close()
        return True
    except Exception as e:
        ner_logger.error("Error in write_file_to_s3 - %s %s %s : %s" % (bucket_name, address, disk_filepath, e))

    return False


def get_s3_connection_and_bucket(bucket_name, bucket_region=None):
    """
    Connect to S3 bucket

    Args:
        bucket_name (str): name of the bucket to upload file to
        bucket_region (str, Optional): region of the s3 bucket, defaults to None

    Returns:
        tuple containing
            boto.s3.connection.S3Connection: Boto connection to s3 in the specified region
            boto.s3.bucket.Bucket: bucket object of the specified name

    """
    if bucket_region:
        connection = boto.s3.connect_to_region(bucket_region)
    else:
        connection = boto.connect_s3()
    bucket = connection.get_bucket(bucket_name)
    return connection, bucket

class CrfModel(object):

    __metaclass__ = Singleton

    def __init__(self, entity_name):
        self.entity_name = entity_name
        self.loaded_model_path_v1 = None
        self.domain_model_dict_v1 = None

    def load_model_v1(self, model_path=None):
        """
        Method that will load model data for domain from s3 using model path store in redis
        :param model_path: (String) Path when model needs to be read locally
        :return: Dictionary of model
        """
        if model_path:
            self.domain_model_dict_v1 = pickle.load(open(model_path, 'rb'))
            return self.domain_model_dict_v1
        s3_model_path_v1 = get_cache_ml(SENTENCE_SIMILARITY_REDIS_MODELS_PATH_V1 + self.domain_name)
        if s3_model_path_v1 == self.loaded_model_path_v1:
            if not self.domain_model_dict_v1:
                self.domain_model_dict_v1 = self._read_model_data(s3_model_path_v1)
        else:
            self.domain_model_dict_v1 = self._read_model_data(s3_model_path_v1)
            self.loaded_model_path_v1 = s3_model_path_v1
        return self.domain_model_dict_v1
