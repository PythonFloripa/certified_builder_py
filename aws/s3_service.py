from aws.boto_aws import get_instance_aws, ServiceNameAWS
from config import config
import logging

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.aws = get_instance_aws(ServiceNameAWS.S3)
        self.bucket_name = config.BUCKET_NAME

    def upload_file(self, file_path: str, key: str):
        try:
            response = self.aws.upload_file(file_path, self.bucket_name, key)
            logger.info(
                f"Arquivo {file_path} enviado para o bucket {self.bucket_name} com sucesso"
            )
        except Exception as e:
            logger.error(
                f"Erro ao enviar o arquivo {file_path} para o bucket {self.bucket_name}: {e}"
            )
            raise e
