
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
import datetime
from oauth2client.file import Storage
import rfc3339      # for date object -> date string
import iso8601      # for date string -> date object
import pytz
import time

def get_date_object(date_string):
    return iso8601.parse_date(date_string)

def get_date_string(date_object):
    return rfc3339.rfc3339(date_object)

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'C:\\client_id.json'
APPLICATION_NAME = 'Drive API Python Quickstart'



def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                 'python-drive-sync.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


class DriveIntegration(object):
    
    def __init__(self, team_drive_name=None):
        self.creds = get_credentials()
        self.http = self.creds.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=self.http)
        self.team_drive_id = None
        if team_drive_name:
            self.use_team_drive(team_drive_name)
        

    def use_team_drive(self, td_name, td_id=None):
        if td_id:
            self.team_drive_id = td_id
        else:
            td = self.service.teamdrives().list().execute()
            for t in td["teamDrives"]:
                if t["name"].lower() == td_name.lower():
                    self.team_drive_id = t["id"]
                    break
        if self.team_drive_id == None:
            raise ValueError("Could not find Team Drive '{0}'".format(td_name))
        
    
    def get_files(self, **kwargs):

        if self.team_drive_id:
            td_args = {"corpora":"teamDrive",
                       "supportsTeamDrives":True,
                       "includeTeamDriveItems":True,
                       "teamDriveId":self.team_drive_id}
            if "parent" not in kwargs:
                kwargs["parent"] = self.team_drive_id
        else:
            td_args = {{}}

        
        def encode(**kwargs):
            st = []
            for k, v in kwargs.iteritems():
                if k == "parent":
                    st.append("'{0}' in parents".format(v))
                else:
                    st.append("{0}='{1}'".format(k, v))
            return " and ".join(st)
        
        q = encode(**kwargs)
        

        
        results = self.service.files().list(q=q,
            pageSize=30, fields="nextPageToken, files(id, name,parents,modifiedTime)", **td_args).execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            return items

    def get_folders(self, **kwargs):
        return self.get_files(mimeType='application/vnd.google-apps.folder', **kwargs)
                
    def get_document(self, doc_id):
        doc = self.service.files().get(fileId=doc_id).execute()
        print (doc)

    def sync_google_doc_folder(self,local_path,remote_path):
        
        parent_id = self.get_or_create_path(remote_path)

        files = os.listdir(local_path)
        remote_files = self.get_files(parent=parent_id)
        if remote_files == None:
            remote_files = []
        remote_lookup = {x["name"] + ".md":x for x in remote_files}
        
        for f in files:
            title = os.path.splitext(f)[0]
            path = os.path.join(local_path,f)
            remote = remote_lookup.get(f)
            bst = pytz.timezone('Europe/London')
            our_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            our_time = datetime.datetime(our_time.year,
                                         our_time.month,
                                         our_time.day,
                                         our_time.hour,
                                         our_time.minute,
                                         our_time.second)
            our_time = bst.localize(our_time)

            if remote:
                their_time = get_date_object(remote['modifiedTime'])
                print (f)
                if our_time > their_time:
                    self.upload_google_doc(title,
                                           parent_id=parent_id,
                                           filename=path,
                                           existing_id=remote['id'],
                                           modified_time=our_time)
                elif their_time > our_time:
                    self.download_google_doc(remote['id'],path,their_time)
                else:
                    print ("in sync!")
            else:
                self.upload_google_doc(title,
                                       parent_id=parent_id,
                                       filename=path,
                                       modified_time=our_time
                                       )
                
    
    def upload_file(self, title, parent_id, description="",mime_type="", filename=None,existing_id=None,modified_time=None):
    
        body = {
            'name': title,
            'description': description,
        }
        
        doc_id = None
        existing = None
        if existing_id:
            doc_id = existing_id
            existing = True
        else:
            existing = self.get_files(name=title,parent=parent_id)
            if existing:
                doc_id = existing[0]["id"]
                
        service_function = self.service.files().create
        if doc_id:
            print ("Overriding existing!")
            
            def update_with_id(*args,**kwargs):
                return self.service.files().update(fileId=doc_id,*args,**kwargs)
            service_function = update_with_id
        
        if mime_type:
            body["mimeType"] = mime_type
        # Set the parent folder.
        if parent_id and existing == None:
            body['parents'] = [parent_id]
            
        if modified_time:
            body['modifiedTime'] = get_date_string(modified_time)
        try:
            
            kwargs = {"body":body,
                      "supportsTeamDrives":True}
            if filename:
                media_body = MediaFileUpload(filename,
                                             mimetype='text/plain',
                                             resumable=True)
                kwargs["media_body"] = media_body
            file = service_function(**kwargs
                                            ).execute()
            print ("new file created/updated {0}".format(file["id"]))
            return file["id"]
        except errors.HttpError, error:
            print ('An error occurred: %s' % error)
            return None
    
    def get_or_create_path(self, path, parent_id=None):
        folders = path.split("/")
                
        root = parent_id
        for f in folders:
            print (f)
            root = self.get_or_create_folder(f, root)
        return root
    
    def get_file_text(self, drive_id):
            f = self.service.files().export(fileId=drive_id, mimeType='text/plain').execute()
            text = f[3:]
            return text
    
    def download_google_doc(self,drive_id,local_path,time_stamp=None):
        print ("downloading to {0}".format(local_path))
        text = self.get_file_text(drive_id)
        text = text.replace("\r\n\r\n\r\n","\r\n\r\n")
        with open(local_path,'wb') as f:
            f.write(text)
        if time_stamp:
            utime = time.mktime(time_stamp.timetuple())
            os.utime(local_path,(utime,utime))
    
    def get_or_create_folder(self, title, parent_id=None):

        if parent_id == None and self.team_drive_id:
            parent_id = self.team_drive_id

        if parent_id:
            f = self.get_folders(name=title, parent=parent_id)
        else:
            f = self.get_folders(name=title)
            
        if f:
            return f[0]['id']
        else:
            print ("creating!")
            return self.create_folder(title, parent_id)
                
    def create_folder(self, title, parent_id=None):
        file_metadata = {
              'name' : title,
              'mimeType' : 'application/vnd.google-apps.folder'
            }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        file = self.service.files().create(body=file_metadata,
                                        fields='id',
                                        supportsTeamDrives=True).execute()
        print ("Folder created {0}".format(file["id"]))
        return file["id"]

    def upload_google_doc(self, *args,**kwargs):
        return self.upload_file(*args,
                        mime_type='application/vnd.google-apps.document',
                        **kwargs)
    
