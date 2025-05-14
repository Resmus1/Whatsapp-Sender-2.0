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
        return Contact(data['phone'], data.get('name'), data.get('status', 'pending'))

