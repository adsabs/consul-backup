import os
import sys
import shutil
import filecmp
import unittest
import subprocess
import json
import boto3
from moto import mock_s3

# Data to store in test Consul key/value store
test_data = {'key1':'value1', 'key2':'value2', 'key3':'value3'}
# Name for backup bucket on mocked S3 instance
S3_bucket = 'backup'

def setUpModule():
    'set up Consul cluster'
    p = subprocess.Popen(["setup_consul.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    out, err = p.communicate()
    if err:
        print "Failed starting Docker containers:\n%s" % err

def tearDownModule():
    'clean up Consul cluster: stop and remove Docker containers'
    p = subprocess.Popen(["cleanup_consul.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    out, err = p.communicate()
    if err:
        print "Failed stopping/removing Docker containers:\n%s" % err

class TestConsulBackup(unittest.TestCase):

    def test_consul_backup(self):
        'test making backup of Consul key/value store'
        from utils import get_consul_session
        from utils import get_records_from_consul
        from utils import save_records
        import json
        # Get session
        session = get_consul_session('localhost', '8500')
        # Did we get a proper Consul session object back?
        expected = 'Consul'
        class_name = session.__class__.__name__
        self.assertEqual(class_name, expected)
        # Assuming we successfully connected to the Consul cluster,
        # we should be able to ask for "peers"
        peers = session.status.peers()
        # which should be a list
        self.assertTrue(isinstance(peers, list))
        # of length 3
        self.assertEqual(len(peers), 3)
        # Now add some data to the key/value store
        for key,value in test_data.items():
            session.kv[key] = value
        # Now retrieve the records
        records = get_records_from_consul(session)
        # Did we get the expected data back?
        expected_records = '[["key1", 0, "value1"], ["key2", 0, "value2"], ["key3", 0, "value3"]]'
        self.assertEqual(json.dumps(records), expected_records)
        # Now test file creation
        current_dir = os.path.dirname(os.path.realpath(__file__))
        backup_file = '%s/test_backup.json' % current_dir
        save_records(records, backup_file)
        # Check that the file was created
        self.assertTrue(os.path.exists(backup_file))
        # Now check if its contents are what we expect
        backup = open(backup_file).read().strip()
        self.assertEqual(backup, expected_records)
        # Delete the backup file
        os.remove(backup_file)

    def test_consul_restore(self):
        'test if we can restore a Consul key/value store from backup'
        from utils import get_consul_session
        from utils import get_records_from_consul
        from utils import consul_restore_from_backup
        # File from which to restore backup
        current_dir = os.path.dirname(os.path.realpath(__file__))
        backup_file = '%s/adsabs_consul_kv.2015-10-21.json' % current_dir
        # and check that it really exists
        self.assertTrue(os.path.exists(backup_file))
        # Get session
        session = get_consul_session('localhost', '8500')
        # Did we get a proper Consul session object back?
        expected = 'Consul'
        class_name = session.__class__.__name__
        self.assertEqual(class_name, expected)
        # Assuming we successfully connected to the Consul cluster,
        # we should be able to ask for "peers"
        peers = session.status.peers()
        # which should be a list
        self.assertTrue(isinstance(peers, list))
        # of length 3
        self.assertEqual(len(peers), 3)
        # Restore from backup and then test querying URL
        consul_restore_from_backup(session, backup_file)
        # Get the records from Consul
        records = get_records_from_consul(session)
        # and check whether they are what we expect
        expected_records = '[["key1", 0, "value1"], ["key2", 0, "value2"], ["key3", 0, "value3"]]'
        self.assertEqual(json.dumps(records), expected_records)

    def test_S3_communication(self):
        'test downloading/uploading from/to S3'
        from utils import s3_upload_file
        from utils import s3_download_file
        # Make sure the backup file still exists
        current_dir = os.path.dirname(os.path.realpath(__file__))
        backup_file = '%s/adsabs_consul_kv.2015-10-21.json' % current_dir
        backup_copy = '%s/test_backup.json' % current_dir
        # make a copy to test
        shutil.copyfile(backup_file, backup_copy)
        self.assertTrue(os.path.exists(backup_file))
        with mock_s3():
            # Create the mocked S3 session object
            s3 = boto3.resource('s3')
            # See to it that the expected S3 bucket exists
            s3.create_bucket(Bucket=S3_bucket)
            # Upload the backup file to the mocked S3
            s3_upload_file(s3, backup_copy, S3_bucket)
            # Is the file in the bucket
            bucket_contents = [o.key for o in s3.Bucket(S3_bucket).objects.all()]
            # Is it what we expect?
            expected_contents = [os.path.basename(backup_copy)]
            self.assertEqual(bucket_contents, expected_contents)
            # Now check if we can download the file
            os.remove(backup_copy)
            # It really is no longer there
            self.assertFalse(os.path.exists(backup_copy))
            # Download the file from mocked S3
            s3_download_file(s3, backup_copy, S3_bucket)
            # The file should be back
            self.assertTrue(os.path.exists(backup_copy))
            # and be the same as the original
            self.assertTrue(filecmp.cmp(backup_file, backup_copy, shallow=False))
            # Finally, remove the copy
            os.remove(backup_copy)

if __name__ == '__main__':
    unittest.main()
