from app.database import Base


# All models are imported here so Alembic can discover them
import app.models.user  # noqa
import app.models.role  # noqa
import app.models.dashboard  # noqa
import app.models.chart  # noqa
import app.models.filter  # noqa
