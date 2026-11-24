from redis.exceptions import RedisError
from fastapi import HTTPException

from src.config.resources import cache, engine
from src.services import cases, reviews, runs, tickets
from src.services.tickets import AlreadySwitched, BudgetError, ConcurrentPublication, NotFound


def new_case(data, user):
    with engine.begin() as db:
        return cases.create(db, data, user["username"])


def new_run(case_id, data, user):
    with engine.begin() as db:
        run = runs.enqueue(db, case_id, data.parameter, user["username"])
    try:
        cache.lpush("workbench:wake", str(run["id"]))
        cache.ltrim("workbench:wake", 0, 99)
    except RedisError:
        # The database holds the durable queue. The worker also polls it.
        pass
    return run


def new_review(run_id, data, user):
    with engine.begin() as db:
        return reviews.sign(db, run_id, data, user["username"])


def register_supplementation(case_id, form, user):
    try:
        with engine.begin() as db:
            return tickets.register_supplements(
                db, case_id, [item.model_dump() for item in form.tickets], user["username"]
            )
    except NotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except AlreadySwitched as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def publish_case(case_id, parameter, user, attempts=3):
    for attempt in range(attempts):
        try:
            with engine.begin() as db:
                result, _created = tickets.publish(db, case_id, parameter, user["username"])
                return result
        except NotFound as exc:
            raise HTTPException(404, str(exc)) from exc
        except BudgetError as exc:
            raise HTTPException(422, str(exc)) from exc
        except ConcurrentPublication as exc:
            if attempt == attempts - 1:
                raise HTTPException(409, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    raise HTTPException(409, "该卷已由另一批次完成切换，请刷新后查看")
