import functools
from typing import Any, Callable

from .logging_config import action_logger


def log_action(action_name: str, verbose: bool = False) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            user_id = kwargs.get("user_id") or (args[0] if len(args) > 0 else None)
            currency_code = kwargs.get("currency_code") or kwargs.get("from_code")
            amount = kwargs.get("amount")

            try:

                action_logger.info(
                    f"{action_name} START user_id={user_id}"
                    f"currency={currency_code} amount={amount}"
                )

                result = func(*args, **kwargs)

                if verbose and hasattr(result, "wallet_state"):
                    action_logger.info(
                        f"{action_name} OK user_id={user_id}"
                        f"currency={currency_code} amount={amount}"
                        f"result={result}"
                    )
                else:
                    action_logger.info(
                        f"{action_name} OK user_id={user_id}"
                        f"currency={currency_code} amount={amount}"
                    )

                return result

            except Exception as e:
                action_logger.error(
                    f"{action_name} ERROR user_id={user_id}"
                    f"currency={currency_code} amount={amount}"
                    f"error_type={type(e).__name__} error_message='{str(e)}'"
                )
                raise

        return wrapper
    return decorator
