import os

class Config(object):
  API_ID = int(os.getenv("apiid",7323956))
  
  API_HASH = os.getenv("apihash","890aa74ed297150b3120914946db5c")
  
  BOT_TOKEN = os.getenv("token","758689606:AAGWcM_HcbcRlk7AmnAvQ8xXOMaa1aKwZE")
  
  AUTH = os.getenv("auth","1387186514")
  
  OWNER =os.getenv("owner","1387186514")

  GIT_TK =os.getenv("git_tk","")

  GIT_UN = os.getenv("git_name","")

  GIT_REPO = os.getenv("git_repo","")

  GIT_BRANCH = os.getenv("git_branch","main")

  #TeraExScript = os.getenv("tscript")

  #PW =int(os.getenv("spw"))
