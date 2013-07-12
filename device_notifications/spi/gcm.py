

def send_message(self, message):
    # Do GCM import here to allow users to only use iOS capabilities.
    from gcm import GCM
    gcm = GCM(API_KEY)


