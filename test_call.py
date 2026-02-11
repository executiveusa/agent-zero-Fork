"""Quick test: make a Twilio call with clean TwiML."""
from python.helpers.vault import vault_get
from twilio.rest import Client

sid = vault_get('TWILIO_ACCOUNT_SID')
token = vault_get('TWILIO_AUTH_TOKEN')
from_number = vault_get('TWILIO_PHONE_NUMBER')
to_number = vault_get('ADMIN_PHONE_NUMBER')

client = Client(sid, token)

twiml = (
    '<Response>'
    '<Say voice="Polly.Joanna">'
    'Hello! This is Agent Claw, your autonomous AI assistant. '
    'All systems are operational. Your Twilio voice pipeline is now live. '
    'Credentials have been encrypted in the secure vault. '
    'Security hardening is active. Have a great day!'
    '</Say>'
    '<Pause length="1"/>'
    '<Say voice="Polly.Joanna">Goodbye!</Say>'
    '</Response>'
)

call = client.calls.create(
    to=to_number,
    from_=from_number,
    twiml=twiml,
)
print(f"Call SID: {call.sid}")
print(f"Status: {call.status}")
print(f"From: {from_number} -> To: {to_number}")
