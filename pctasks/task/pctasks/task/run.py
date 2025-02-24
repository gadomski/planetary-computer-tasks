import logging
import os
from importlib.metadata import EntryPoint

from pctasks.core.importer import ensure_code, ensure_requirements
from pctasks.core.logging import RunLogger, TaskLogger
from pctasks.core.models.record import TaskRunStatus
from pctasks.core.models.task import TaskResult, TaskRunMessage
from pctasks.core.storage.blob import BlobStorage, BlobUri
from pctasks.core.tables.record import TaskRunRecordTable
from pctasks.core.utils import environment
from pctasks.task.context import TaskContext
from pctasks.task.settings import TaskSettings
from pctasks.task.task import Task

logger = logging.getLogger(__name__)


class TaskLoadError(Exception):
    pass


class MissingEnvironmentError(Exception):
    pass


def run_task(msg: TaskRunMessage) -> TaskResult:
    task_data, task_config = msg.args, msg.config

    task_settings = TaskSettings.get()

    event_logger = RunLogger(
        task_config.get_run_record_id(),
        app_insights_key=task_config.event_logger_app_insights_key,
    )
    event_logger.log_event(TaskRunStatus.RECEIVED)

    with TaskLogger.from_task_run_config(task_config):

        logger.info(" === PCTasks ===")
        logger.info(f"  == {task_config.get_run_record_id()} ")

        logger.info("  -- PCTasks: Setting up task...")

        task_context = TaskContext.from_task_run_config(task_config)

        try:
            # Setup output storage
            output_blob_config = task_config.output_blob_config
            output_blob_uri = BlobUri(output_blob_config.uri)
            output_path = output_blob_uri.blob_name
            if not output_path:
                raise ValueError(f"Invalid output blob uri: {output_blob_config.uri}")

            output_storage = BlobStorage.from_uri(
                blob_uri=output_blob_uri.base_uri,
                sas_token=output_blob_config.sas_token,
                account_url=output_blob_config.account_url,
            )

            code_requirements_blob_config = task_config.code_requirements_blob_config
            if code_requirements_blob_config:
                req_blob_uri = BlobUri(code_requirements_blob_config.uri)
                req_path = req_blob_uri.blob_name
                if not req_path:
                    raise ValueError(f"Invalid code blob uri: {req_blob_uri}")
                req_storage = BlobStorage.from_uri(
                    blob_uri=req_blob_uri.base_uri,
                    sas_token=code_requirements_blob_config.sas_token,
                    account_url=code_requirements_blob_config.account_url,
                )
                ensure_requirements(
                    req_path,
                    req_storage,
                    task_config.code_pip_options,
                    target_dir=task_settings.code_dir,
                )

            code_src_blob_config = task_config.code_src_blob_config
            if code_src_blob_config:
                code_blob_uri = BlobUri(code_src_blob_config.uri)
                code_path = code_blob_uri.blob_name
                if not code_path:
                    raise ValueError(
                        f"Invalid code blob uri: {code_src_blob_config.uri}"
                    )
                code_storage = BlobStorage.from_uri(
                    blob_uri=code_blob_uri.base_uri,
                    sas_token=code_src_blob_config.sas_token,
                    account_url=code_src_blob_config.account_url,
                )
                ensure_code(code_path, code_storage, target_dir=task_settings.code_dir)

            with TaskRunRecordTable.from_sas_token(
                account_url=task_config.task_runs_table_config.account_url,
                sas_token=task_config.task_runs_table_config.sas_token,
                table_name=task_config.task_runs_table_config.table_name,
            ) as runs_table:
                task_run = runs_table.get_record(task_config.get_run_record_id())
                if task_run is None:
                    raise ValueError(
                        "Could not find task run for "
                        f"job_id={task_config.job_id} "
                        f"run_id={task_config.run_id} "
                        f"task_id={task_config.task_id}"
                    )

                def update_status(status: TaskRunStatus) -> None:
                    assert task_run
                    assert runs_table
                    task_run.update_status(status)
                    runs_table.update_record(task_run)
                    event_logger.log_event(status)

                update_status(TaskRunStatus.STARTING)

                try:
                    task_path = task_config.task

                    entrypoint = EntryPoint("", task_path, "")
                    try:
                        task = entrypoint.load()
                        if callable(task):
                            task = task()
                    except Exception as e:
                        raise TaskLoadError(f"Failed to load task: {task_path}") from e

                    if not isinstance(task, Task):
                        raise TaskLoadError(
                            f"{task_path} of type {type(task)} {task} "
                            f"is not an instance of {Task}"
                        )

                    # Set environment variables
                    if task_config.environment:
                        logger.info(
                            "  Using the following environment variables "
                            "from task configuration:"
                        )
                        logger.info("    " + ",".join(task_config.environment.keys()))

                    with environment(**(task_config.environment or {})):
                        missing_env = []
                        for env_var in task.get_required_environment_variables():
                            if env_var not in os.environ:
                                missing_env.append(env_var)
                        if missing_env:
                            missing_env_str = ", ".join(f'"{e}"' for e in missing_env)
                            raise MissingEnvironmentError(
                                "The task cannot run due to the following "
                                f"missing environment variables: {missing_env_str}"
                            )

                        update_status(TaskRunStatus.RUNNING)
                        logger.info("  -- PCTasks: Running task...")
                        result = task.parse_and_run(task_data, task_context)

                    logger.info("  -- PCTasks: Handling task result...")

                    # Write output to blob storage
                    output_storage.write_text(output_path, result.json(indent=2))

                    update_status(TaskRunStatus.COMPLETED)
                    logger.info(" === PCTasks: Task completed! ===")

                    return result

                except Exception:
                    update_status(TaskRunStatus.FAILED)
                    raise

        except Exception as e:
            logger.info(" === PCTasks: Task Failed! ===")
            logger.exception(e)
            raise
