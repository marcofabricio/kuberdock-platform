"""add versions to predefined_applications

Revision ID: 3e7a44cbe1e2
Revises: 50e4a32fa6c3
Create Date: 2016-09-08 13:30:48.254760

"""

# revision identifiers, used by Alembic.
revision = '3e7a44cbe1e2'
down_revision = '50e4a32fa6c3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Session = sessionmaker()
Base = declarative_base()


class PredefinedApp(Base):
    __tablename__ = 'predefined_apps'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True,
                   nullable=False)
    template = sa.Column(sa.Text, nullable=False)
    created = sa.Column(sa.DateTime, nullable=True)
    modified = sa.Column(sa.DateTime, nullable=True)


class PredefinedAppTemplate(Base):
    __tablename__ = 'predefined_app_templates'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True,
                   nullable=False)
    predefined_app_id = sa.Column(sa.Integer,
                                  sa.ForeignKey("predefined_apps.id"),
                                  nullable=False)
    template = sa.Column(sa.Text, nullable=False)
    active = sa.Column(sa.Boolean, default=False, nullable=False)
    switching_allowed = sa.Column(sa.Boolean, default=True, nullable=False)
    is_deleted = sa.Column(sa.Boolean, default=False, nullable=False)
    created = sa.Column(sa.DateTime, nullable=True)
    modified = sa.Column(sa.DateTime, nullable=True)

    __table_args__ = (
        sa.Index('predefined_app_id_active', 'predefined_app_id', 'active',
                 unique=True, postgresql_where=active),
        sa.CheckConstraint('NOT (active AND is_deleted)'),
    )


class Pod(Base):
    __tablename__ = 'pods'

    id = sa.Column(postgresql.UUID, primary_key=True, nullable=False)
    template_id = sa.Column(sa.Integer, nullable=True)
    template_version_id = sa.Column(sa.Integer, nullable=True)


def upgrade_data(session):
    q = session.query(PredefinedApp)
    for item in q:
        tpl = PredefinedAppTemplate(predefined_app_id=item.id,
                                    template=item.template,
                                    created=item.created,
                                    modified=item.modified,
                                    active=True,
                                    switching_allowed=True)
        session.add(tpl)
    for pod in session.query(Pod).filter(Pod.template_id.isnot(None)).all():
        version = session.query(PredefinedAppTemplate).filter(
            PredefinedAppTemplate.active,
            PredefinedAppTemplate.predefined_app_id == pod.template_id,
        ).first()
        if version is not None:
            pod.template_version_id = version.id
    session.commit()


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    PredefinedAppTemplate.__table__.create(bind)
    op.add_column(u'pods', sa.Column(
        'template_version_id', sa.Integer, nullable=True))

    upgrade_data(session)

    op.drop_column(u'predefined_apps', 'template')
    op.add_column(u'predefined_apps', sa.Column('is_deleted',
                                                sa.Boolean,
                                                server_default='False',
                                                nullable=False)
                  )


def downgrade_data(bind):
    session = Session(bind=bind)
    q = session.query(PredefinedAppTemplate).filter(
        PredefinedAppTemplate.active.is_(True))
    for item in q:
        pa = session.query(PredefinedApp).filter(
            PredefinedApp.id == item.predefined_app_id).first()
        pa.template = item.template
    session.commit()


def downgrade():
    bind = op.get_bind()
    Base.metadata.bind = bind
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'predefined_apps', sa.Column('template', sa.TEXT(),
                                                nullable=True))
    op.drop_column(u'predefined_apps', 'is_deleted')

    downgrade_data(bind)

    op.alter_column(u'predefined_apps', u'template', nullable=False)

    op.drop_column(u'pods', 'template_version_id')
    op.drop_table('predefined_app_templates')
    ### end Alembic commands ###