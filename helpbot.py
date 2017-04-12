from __future__ import print_function
import httplib2
import os
import time
import datetime

from slackclient import SlackClient
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import print_bot_id 

# startebot's ID as an enviroment variable
os.environ['BOT_ID'] = 'U4YDS015M'
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
WORKS_COMMAND = "calendar"
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'HelpBot'

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def handle_command(command, channel):
	"""
	Received commands directed at the bot and determines if they
	are valid commands. If so, then acts on the commands. If not,
	returns back what it nedds for clarification.
	"""
	response = "Not sure what you mean. Use the *" + WORKS_COMMAND + \
	           "* command and look what I can"
	if command.startswith(WORKS_COMMAND):
		response = main()
	slack_client.api_call("chat.postMessage", channel=channel,
		                   text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
	"""
	The Slack Real Time Messaging API is an events firehose.
	this parsing function returns None unless a message is
	directed at the Bot, based on its ID.
	"""
	output_list = slack_rtm_output
	if output_list and len(output_list) > 0:
		for output in output_list:
			if output and 'text' in output and AT_BOT in output['text']:
				# return text after the @ mention, whitespace removed
				return output['text'].split(AT_BOT)[1].strip().lower(), \
				       output['channel']
	return None, None

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
                                   'calendar-python-helpbot.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        # print('Storing credentials to ' + credential_path)
        # response = 'Storing credentials to ' + credential_path
        # slack_client.api_call("chat.postMessage", channel=channel,
		#                    text=response, as_user=True)
    return credentials

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + ' ' #'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    text = 'Getting the upcoming 10 events'
    slack_client.api_call("chat.postMessage", channel=channel,
		                   text=text, as_user=True)
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        # print('No upcoming events found.')
        text = 'No upcoming events found.'
        slack_client.api_call("chat.postMessage", channel=channel,
		                   text=text, as_user=True)
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        #print(start, event['summary'])
        text = start + event['summary']
        slack_client.api_call("chat.postMessage", channel=channel,
		                   text=text, as_user=True)


if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
	if slack_client.rtm_connect():
		print("HelpBot connected and running!")
		while True:
			command, channel = parse_slack_output(slack_client.rtm_read())
			if command and channel:
				handle_command(command, channel)
			time.sleep(READ_WEBSOCKET_DELAY)
	else:
		print("Connection failed. Invalid Slack token or bot ID?")
