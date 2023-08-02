import os
import boto3

class FileHandler:
    def __init__(self, storage_type='local', bucket_name=None):
        """
        Initialize the FileHandler with the specified storage type.
        
        Args:
            storage_type (str): The storage type, either 'local' or 's3'.
            bucket_name (str): The name of the S3 bucket (only required if storage_type is 's3').
        """
        self.storage_type = storage_type
        self.bucket_name = bucket_name
        self.s3 = None
        
        if self.storage_type == 's3':
            if not self.bucket_name:
                raise ValueError("S3 bucket name must be provided when using 's3' storage.")
            self.s3 = boto3.resource('s3')
    
    def create_file(self, file_name, content):
        """
        Create a new file with the given name and content.
        
        Args:
            file_name (str): The name of the file.
            content (str): The content to write to the file.
        """
        if self.storage_type == 'local':
            with open(file_name, 'w') as file:
                file.write(content)
        elif self.storage_type == 's3':
            self.s3.Object(self.bucket_name, file_name).put(Body=content)
        else:
            raise ValueError("Invalid storage type. Use 'local' or 's3'.")
    
    def read_file(self, file_name):
        """
        Read the content of the specified file.
        
        Args:
            file_name (str): The name of the file to read.
        
        Returns:
            str: The content of the file.
        """
        if self.storage_type == 'local':
            with open(file_name, 'r') as file:
                content = file.read()
        elif self.storage_type == 's3':
            obj = self.s3.Object(self.bucket_name, file_name)
            content = obj.get()['Body'].read().decode('utf-8')
        else:
            raise ValueError("Invalid storage type. Use 'local' or 's3'.")
        
        return content
    
    def update_file(self, file_name, new_content):
        """
        Update the content of an existing file.
        
        Args:
            file_name (str): The name of the file to update.
            new_content (str): The new content to write to the file.
        """
        if self.storage_type == 'local':
            with open(file_name, 'w') as file:
                file.write(new_content)
        elif self.storage_type == 's3':
            self.s3.Object(self.bucket_name, file_name).put(Body=new_content)
        else:
            raise ValueError("Invalid storage type. Use 'local' or 's3'.")
    
    def delete_file(self, file_name):
        """
        Delete the specified file.
        
        Args:
            file_name (str): The name of the file to delete.
        """
        if self.storage_type == 'local':
            if os.path.exists(file_name):
                os.remove(file_name)
            else:
                raise FileNotFoundError(f"File '{file_name}' not found.")
        elif self.storage_type == 's3':
            self.s3.Object(self.bucket_name, file_name).delete()
        else:
            raise ValueError("Invalid storage type. Use 'local' or 's3'.")


# Usage:

# Local storage CRUD

# handler = FileHandler(storage_type='local')
# handler.create_file('local_file.txt', 'This is content for the local file.')
# print(handler.read_file('local_file.txt'))
# handler.update_file('local_file.txt', 'Updated content for the local file.')
# print(handler.read_file('local_file.txt'))
# handler.delete_file('local_file.txt')

# # S3 CRUD

# # Set up AWS credentials using `boto3.setup_default_session()` or ENV VARS.

# handler = FileHandler(storage_type='s3', bucket_name='your_s3_bucket_name')
# handler.create_file('s3_file.txt', 'This is content for the S3 file.')
# print(handler.read_file('s3_file.txt'))
# handler.update_file('s3_file.txt', 'Updated content for the S3 file.')
# print(handler.read_file('s3_file.txt'))
# handler.delete_file('s3_file.txt')