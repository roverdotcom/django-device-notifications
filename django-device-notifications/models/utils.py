from django.db.models.fields import Field


class DynamicDefaultField(Field):
    def __init__(self, *args, **kwargs):
        super(DynamicDefaultField, self).__init__(self, *args, **kwargs)
        
