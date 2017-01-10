# hashmap to keep track of past uids
# so we don't generate the same one twice
uids = {}
def rand_string(r):
  return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(r))

def gen_uid():
  r = 7
  uid = rand_string(r)
  while uid in uids:
    uid = rand_string(r)
  return uid

def wrap_message(action, uid, *args):
    args = [str(arg) for arg in args]
    args_string = "&".join(args)
    return "{0}?{1}&{2}".format(action, uid, args_string)

def unwrap_message(msg):
    action, args_string = msg.split('?')
    uid, args = args_string.split('&')
    return action, uid, args
