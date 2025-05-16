class Contact:
    def __init__(self, phone, name=None, status='pending'):
        self.name = name
        self.phone = phone
        self.status = status

    def to_dict(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        return Contact(data['phone'], data.get('name'), data['status'])


class Image:
    def __init__(self, url, category=None):
        self.url = url
        self.category = category


    def to_dict(self):
        return {
            'url': self.url,
            'category': self.category,
        }
    
    @staticmethod
    def from_dict(data):
        return Image(data['url'], data.get('category'))
