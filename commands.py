from workflow.notify import notify
from workflow import PasswordNotFound

SERVICE_NAME = 'app.getguru.com.'

def _extract_parameter(query):
  is_parameter_present = len(query) == 5
  return None if not is_parameter_present else query[4]

def _delete_secret(wf, type):
  try:
    wf.delete_password(wf.settings['account'], SERVICE_NAME + type)
  except:
    pass

def set_email(wf, query):
  parameter = _extract_parameter(query)
  wf.settings['account'] = parameter
  notify(
    title='Email successfully set',
    text='Email was set to "' + wf.settings['account'] + '"'
  )

def secret_setter_generator(type):
  def set_secret(wf, query):
    parameter = _extract_parameter(query)
    wf.save_password(wf.settings['account'], parameter, SERVICE_NAME + type)
    notify(
      title=type.capitalize() + ' successfully set',
      text=type.capitalize() + ' was set in Keychain'
    )
  return set_secret

def delete_settings(wf, _query):
  is_account_set = 'account' in wf.settings
  if is_account_set:
    _delete_secret(wf, 'password')
    _delete_secret(wf, 'token')
  wf.clear_settings()
  wf.clear_cache()
  notify(
    title='All settings deleted',
    text='Email, password and/or token deleted from persistent settings and Keychain'
  )

commands = {
  'set email': {
    'title': 'set email <email>',
    'subtitle': 'Set email for Guru',
    'needs_parameter': True,
    'handler': set_email
  },
  'set password': {
    'title': 'set password <password>',
    'subtitle': 'Set your password in the Keychain to be used for Guru',
    'needs_parameter': True,
    'handler': secret_setter_generator('password')
  },
  'set token': {
    'title': 'set token <token>',
    'subtitle': 'Set API token for Guru (will be faster than using the password)',
    'needs_parameter': True,
    'handler': secret_setter_generator('token')
  },
  'delete settings': {
    'title': 'delete settings',
    'subtitle': 'Deletes the email, password, and token',
    'needs_parameter': False,
    'handler': delete_settings
  }
}