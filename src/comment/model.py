from datetime import datetime

class Comment:
    def __init__(self, content, author_id, artwork_id, created_at=None):
        self.content = content
        self.author_id = author_id
        self.artwork_id = artwork_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = self.created_at
        self._id = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    def edit_content(self, new_content):
        self.content = new_content
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id': getattr(self, 'id', None),
            'content': self.content,
            'author_id': self.author_id,
            'artwork_id': self.artwork_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __str__(self):
        return f"Comment(content={self.content[:30]}...)" 