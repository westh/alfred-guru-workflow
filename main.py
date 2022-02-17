import sys
import json
from workflow import Workflow, web, PasswordNotFound
from commands import commands

SERVICE_NAME = 'app.getguru.com.'
BASE_URL = 'https://api.getguru.com'

def get_fresh_user_token(wf):
  try:
    password = wf.get_password(wf.settings['account'], SERVICE_NAME + 'password')
  except PasswordNotFound:
    return None

  r = web.post(
    BASE_URL + '/auth/login',
    headers={
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Origin': 'https://app.getguru.com' # won't work without it
    },
    data=json.dumps({
      'email': wf.settings['account'],
      'password': password
    })
  )
  r.raise_for_status()

  data = r.json()
  guru_user_token = data['token']
  wf.cache_data('guru_user_token', guru_user_token)
  return guru_user_token

def get_cached_user_token(wf):
  try:
    token = wf.get_password(wf.settings['account'], SERVICE_NAME + 'token')
    if (token != None):
      return token
  except PasswordNotFound:
    guru_user_token = wf.cached_data('guru_user_token', max_age=4 * 60 * 60)
    if (not wf.cached_data_fresh('guru_user_token', max_age=4 * 60 * 60)):
      guru_user_token = get_fresh_user_token(wf)
    return guru_user_token

def get_cards(query, user_token):
  cards = web.post(
    BASE_URL + '/api/v1/search/query',
    data=json.dumps({
      'searchTerms': query
    }),
    headers={
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    auth=(wf.settings['account'], user_token)
  )
  return cards

def command_handler(wf, query):
  requested_command = '' if len(query) <= 2 else ' '.join(query[2:4])
  filtered_commands = wf.filter(requested_command, list(commands.keys()))

  is_no_command_found = len(filtered_commands) == 0
  if (is_no_command_found):
    wf.add_item(
      title='No commands found for "' + requested_command + '"',
      valid=False
    )
    wf.send_feedback()
    return

  is_parameter_present = len(query) == 5
  for command in filtered_commands:
    is_valid = (not commands[command]['needs_parameter'] and len(query) == 4) or is_parameter_present
    wf.add_item(
      title='> ' + commands[command]['title'],
      subtitle=commands[command]['subtitle'],
      autocomplete='> ' + command + ' ',
      arg=' '.join(query[1:]),
      valid=is_valid
    )
  wf.send_feedback()
  return

def main(wf):
  query = sys.argv
  is_action = query[1] == '>'
  if (is_action):
    command_handler(wf, query)
    return

  user_token = get_cached_user_token(wf)

  is_token_or_password_set = user_token != None
  if (not is_token_or_password_set):
    wf.add_item(
      title='Neither token or password has been set',
      valid=False
    )
    wf.send_feedback()
    return

  search_term = query[1] if len(query) == 1 else ' '.join(query[1:])
  search_term = search_term.decode('utf-8')
  cards_response = get_cards(search_term, user_token)
  is_denied_due_to_auth = cards_response.status_code == 401
  if (is_denied_due_to_auth):
    user_token = get_fresh_user_token(wf)
    cards_response = get_cards(search_term, user_token)

  cards_response.raise_for_status()
  cards = cards_response.json()

  is_no_card_found = len(cards) == 0
  if (is_no_card_found):
    wf.add_item(
      title='No cards found for "' + search_term + '"',
      valid=False
    )
    wf.send_feedback()
    return

  for card in cards:
    card_url = 'https://app.getguru.com/card/' + card['slug']
    wf.add_item(
      title=card['preferredPhrase'],
      subtitle=card_url,
      arg=card_url,
      valid=True
    )
  wf.send_feedback()

if __name__ == u"__main__":
  wf = Workflow()
  sys.exit(wf.run(main))
