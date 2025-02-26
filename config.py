import os

class Config(object):
  API_ID = int(os.getenv("apiid",7322056))
  
  API_HASH = os.getenv("apihash","89074aa74ed297150b3120914946db5c")
  
  BOT_TOKEN = os.getenv("token","7853381482:AAG3fe7mz1vLR47fJ7_GYi8bWM2XcCvJ5Vo")
  
  AUTH = os.getenv("auth","1387186514")
  
  OWNER =os.getenv("owner","1387186514")

  #TeraExScript = os.getenv("tscript")

  #PW =int(os.getenv("spw"))
