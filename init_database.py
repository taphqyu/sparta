import sqlalchemy

import model

if __name__ == '__main__':
    engine = sqlalchemy.create_engine('sqlite:///sparta.db')
    model.Base.metadata.create_all(engine)
