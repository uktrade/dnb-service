from authbroker_client.backends import AuthbrokerBackend

class CustomAuthbrokerBackend(AuthbrokerBackend):
    
    @staticmethod
    def get_profile_id_name():
        return "email"