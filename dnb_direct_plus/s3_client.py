import logging
import os

from boto3 import client

from django.conf import settings


logger = logging.getLogger(__name__)


class S3Client:
    """
    Interface for interacting with the S3 Client.
    """

    s3_client = None

    def __init__(self) -> None:
        self.s3_client = client(
            "s3",
            aws_access_key_id=settings.DEFAULT_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.DEFAULT_AWS_SECRET_ACCESS_KEY,
        )
        super().__init__()

    def list_files(self, bucket: str) -> list[str]:
        """
        Returns a list of all the files in the given bucket string.
        """
        return [
            item["Key"]
            for item in self.s3_client.list_objects(Bucket=bucket)["Contents"]
        ]

    def archive_file(self, file_name: str) -> None:
        """
        Moves a file into the archive folder and then deletes it from its
        existing location.
        """
        self.s3_client.Object(
            settings.DNB_MONITORING_S3_BUCKET,
            os.path.join(settings.DNB_ARCHIVE_PATH, file_name),
        ).copy_from(CopySource=f"{settings.DNB_MONITORING_S3_BUCKET}/{file_name}")

        self.s3_client.Object(settings.DNB_MONITORING_S3_BUCKET, file_name).delete()
