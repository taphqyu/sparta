import hashlib

from sqlalchemy import Column, Enum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import backref, relationship

from model_base import Base, JsonEncodedList, JsonEncodedImmutable

class Project(Base):
    __tablename__       = 'Projects'

    project_id          = Column(Integer, primary_key=True)
    name                = Column(String, unique=True)
    fetch_url           = Column(String)
    branchlink_url      = Column(String)
    commitlink_url      = Column(String)

class Review(Base):
    __tablename__       = 'Reviews'

    review_id           = Column(Integer, primary_key=True)
    project_id          = Column(Integer, ForeignKey('Projects.project_id'))
    title               = Column(String)
    status              = Column(Enum('new', 'in_review', 'rework', 'completed', 'canceled'))
    authors             = Column(JsonEncodedList.as_mutable(JsonEncodedImmutable))
    reviewers           = Column(JsonEncodedList.as_mutable(JsonEncodedImmutable))
    observers           = Column(JsonEncodedList.as_mutable(JsonEncodedImmutable))

    project             = relationship('Project')

class Round(Base):
    __tablename__       = 'Rounds'

    round_id            = Column(Integer, primary_key=True)
    review_id           = Column(Integer, ForeignKey('Reviews.review_id'))
    round_index         = Column(Integer)

    merge_base_branch   = Column(String) # TODO: rename to merge_base_name
    merge_base_commit   = Column(String(40))

    branch_tip_name     = Column(String)
    branch_tip_commit   = Column(String(40))

    prev_tip_name       = Column(String)
    prev_tip_commit     = Column(String(40))

    review              = relationship('Review', backref=backref('rounds', order_by=round_index), foreign_keys=review_id)
    changes             = relationship('Change')

class Change(Base):
    __tablename__       = 'Changes'

    change_id           = Column(Integer, primary_key=True)
    round_id            = Column(Integer, ForeignKey('Rounds.round_id'))

    merge_base_file_id  = Column(Integer, ForeignKey('Files.file_id'))
    branch_tip_file_id  = Column(Integer, ForeignKey('Files.file_id'))
    prev_tip_file_id    = Column(Integer, ForeignKey('Files.file_id'))

    status_from_base    = Column(String(1))
    status_from_prev    = Column(String(1))

    # TODO: make sure these load lazily
    merge_base_file     = relationship('File', foreign_keys=merge_base_file_id)
    branch_tip_file     = relationship('File', foreign_keys=branch_tip_file_id)
    prev_tip_file       = relationship('File', foreign_keys=prev_tip_file_id)

    round               = relationship('Round')

class File(Base):
     __tablename__      = 'Files'

     file_id            = Column(Integer, primary_key=True)
     path               = Column(String)
     contents           = Column(LargeBinary)
     content_hash       = Column(String(40), unique=True)

     @classmethod
     def find_or_create(cls, session, path, contents):
        content_hash = hashlib.sha1(path + contents).hexdigest()
        existing = session.query(File).filter_by(content_hash=content_hash).first()

        if existing is None:
            return File(path=path, contents=contents, content_hash=content_hash)
        else:
            return existing
