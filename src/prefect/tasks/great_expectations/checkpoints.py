"""
Great Expectations checkpoints are combinations of data source, expectation suite, and
validation operators configuration that can be used to run Great Expectations actions.
Checkpoints are the preferred deployment of validation configuration; you can read more about
setting up checkpoints [at the Great Expectation
docs](https://docs.greatexpectations.io/en/latest/tutorials/getting_started/set_up_your_first_checkpoint.html#set-up-your-first-checkpoint).

You can use these task library tasks to interact with your Great Expectations checkpoint from a
Prefect flow.
"""
from typing import Optional

import prefect
from prefect import Task
from prefect.backend.artifacts import create_markdown_artifact

from prefect.engine import signals
from prefect.utilities.tasks import defaults_from_attrs

import great_expectations as ge


class RunGreatExpectationsValidation(Task):
    """
    Task for running data validation with Great Expectations.

    Example using the GE getting started tutorial:
    https://github.com/superconductive/ge_tutorials/tree/main/ge_getting_started_tutorial

    The task can be used to run validation in one of the following ways:

    1. expectation_suite AND batch_kwargs, where batch_kwargs is a dict
    2. assets_to_validate: a list of dicts of expectation_suite + batch_kwargs
    3. checkpoint_name: the name of a pre-configured checkpoint (which bundles expectation suites
    and batch_kwargs)

    ```python
    from prefect import task, Flow, Parameter
    from prefect.tasks.great_expectations import RunGreatExpectationsValidation


    # Define checkpoint task
    validation_task = RunGreatExpectationsValidation()


    # Task for retrieving batch kwargs including csv dataset
    @task
    def get_batch_kwargs(datasource_name, dataset):
        dataset = ge.read_csv(dataset)
        return {"dataset": dataset, "datasource": datasource_name}


    with Flow("ge_test") as flow:
        datasource_name = Parameter("datasource_name")
        dataset = Parameter("dataset")
        batch_kwargs = get_batch_kwargs(datasource_name, dataset)

        expectation_suite_name = Parameter("expectation_suite_name")
        prev_run_row_count = 100  # can be taken eg. from Prefect KV store
        validation_task(
            batch_kwargs=batch_kwargs,
            expectation_suite_name=expectation_suite_name,
            evaluation_parameters=dict(prev_run_row_count=prev_run_row_count)
        )

    flow.run(
        parameters={
            "datasource_name": "data__dir",
            "dataset": "data/yellow_tripdata_sample_2019-01.csv",
            "expectation_suite_name": "yellow_tripdata_sample_2019-01.warning",
        },
    )
    ```


    Args:
        - checkpoint_name (str, optional): the name of a pre-configured checkpoint; should match the
            filename of the checkpoint without .py
        - context (DataContext, optional): an in-memory GE DataContext object. e.g.
            `ge.data_context.DataContext()` If not provided then `context_root_dir` will be used to
            look for one.
        - assets_to_validate (list, optional): A list of assets to validate when running the
            validation operator.
        - batch_kwargs (dict, optional): a dictionary of batch kwargs to be used when validating
            assets.
        - expectation_suite_name (str, optional): the name of an expectation suite to be used when
            validating assets.
        - context_root_dir (str, optional): the absolute or relative path to the directory holding
            your `great_expectations.yml`
        - runtime_environment (dict, optional): a dictionary of great expectation config key-value
            pairs to overwrite your config in `great_expectations.yml`
        - run_name (str, optional): the name of this  Great Expectation validation run; defaults to
            the task slug
        - run_info_at_end (bool, optional): add run info to the end of the artifact generated by this
            task. Defaults to `True`.
        - disable_markdown_artifact (bool, optional): toggle the posting of a markdown artifact from
            this tasks. Defaults to `False`.
        - validation_operator (str, optional): configure the actions to be executed after running
            validation. Defaults to `action_list_operator`
        - evaluation_parameters (Optional[dict], optional): the evaluation parameters to use when
            running validation. For more information, see
            [example](https://docs.prefect.io/api/latest/tasks/great_expectations.html#rungreatexpectationsvalidation)
            and
            [docs](https://docs.greatexpectations.io/en/latest/reference/core_concepts/evaluation_parameters.html).
        - **kwargs (dict, optional): additional keyword arguments to pass to the Task constructor
    """

    def __init__(
        self,
        checkpoint_name: str = None,
        context: "ge.DataContext" = None,
        assets_to_validate: list = None,
        batch_kwargs: dict = None,
        expectation_suite_name: str = None,
        context_root_dir: str = None,
        runtime_environment: Optional[dict] = None,
        run_name: str = None,
        run_info_at_end: bool = True,
        disable_markdown_artifact: bool = False,
        validation_operator: str = "action_list_operator",
        evaluation_parameters: Optional[dict] = None,
        **kwargs
    ):
        self.checkpoint_name = checkpoint_name
        self.context = context
        self.assets_to_validate = assets_to_validate
        self.batch_kwargs = batch_kwargs
        self.expectation_suite_name = expectation_suite_name
        self.context_root_dir = context_root_dir
        self.runtime_environment = runtime_environment or dict()
        self.run_name = run_name
        self.run_info_at_end = run_info_at_end
        self.disable_markdown_artifact = disable_markdown_artifact
        self.validation_operator = validation_operator
        self.evaluation_parameters = evaluation_parameters

        super().__init__(**kwargs)

    @defaults_from_attrs(
        "checkpoint_name",
        "context",
        "assets_to_validate",
        "batch_kwargs",
        "expectation_suite_name",
        "context_root_dir",
        "runtime_environment",
        "run_name",
        "run_info_at_end",
        "disable_markdown_artifact",
        "validation_operator",
        "evaluation_parameters",
    )
    def run(
        self,
        checkpoint_name: str = None,
        context: "ge.DataContext" = None,
        assets_to_validate: list = None,
        batch_kwargs: dict = None,
        expectation_suite_name: str = None,
        context_root_dir: str = None,
        runtime_environment: Optional[dict] = None,
        run_name: str = None,
        run_info_at_end: bool = True,
        disable_markdown_artifact: bool = False,
        validation_operator: str = "action_list_operator",
        evaluation_parameters: Optional[dict] = None,
    ):
        """
        Task run method.

        Args:
            - checkpoint_name (str, optional): the name of the checkpoint; should match the filename of
                the checkpoint without .py
            - context (DataContext, optional): an in-memory GE DataContext object. e.g.
                `ge.data_context.DataContext()` If not provided then `context_root_dir` will be used to
                look for one.
            - assets_to_validate (list, optional): A list of assets to validate when running the
                validation operator.
            - batch_kwargs (dict, optional): a dictionary of batch kwargs to be used when validating
                assets.
            - expectation_suite_name (str, optional): the name of an expectation suite to be used when
                validating assets.
            - context_root_dir (str, optional): the absolute or relative path to the directory holding
                your `great_expectations.yml`
            - runtime_environment (dict, optional): a dictionary of great expectation config key-value
                pairs to overwrite your config in `great_expectations.yml`
            - run_name (str, optional): the name of this  Great Expectation validation run; defaults to
                the task slug
            - run_info_at_end (bool, optional): add run info to the end of the artifact generated by this
                task. Defaults to `True`.
            - disable_markdown_artifact (bool, optional): toggle the posting of a markdown artifact from
                this tasks. Defaults to `False`.
            - evaluation_parameters (Optional[dict], optional): the evaluation parameters to use when
                running validation. For more information, see
                [example](https://docs.prefect.io/api/latest/tasks/great_expectations.html#rungreatexpectationsvalidation)
                and
                [docs](https://docs.greatexpectations.io/en/latest/reference/core_concepts/evaluation_parameters.html).
            - validation_operator (str, optional): configure the actions to be executed after running
                validation. Defaults to `action_list_operator`.

        Raises:
            - 'signals.FAIL' if the validation was not a success

        Returns:
            - result
                ('great_expectations.validation_operators.types.validation_operator_result.ValidationOperatorResult'):
                The Great Expectations metadata returned from the validation

        """

        runtime_environment = runtime_environment or dict()

        # Load context if not provided directly
        if not context:
            context = ge.DataContext(
                context_root_dir=context_root_dir,
                runtime_environment=runtime_environment,
            )

        # Check that the parameters are mutually exclusive
        if (
            sum(
                bool(x)
                for x in [
                    (expectation_suite_name and batch_kwargs),
                    assets_to_validate,
                    checkpoint_name,
                ]
            )
            != 1
        ):
            raise ValueError(
                "Exactly one of expectation_suite_name + batch_kwargs, assets_to_validate, or "
                "checkpoint_name is required to run validation."
            )

        # If assets are not provided directly through `assets_to_validate` then they need be loaded
        #   if a checkpoint_name is supplied, then load suite and batch_kwargs from there
        #   otherwise get batch from `batch_kwargs` and `expectation_suite_name`

        if not assets_to_validate:
            assets_to_validate = []
            if checkpoint_name:
                ge_checkpoint = context.get_checkpoint(checkpoint_name)

                for batch in ge_checkpoint["batches"]:
                    batch_kwargs = batch["batch_kwargs"]
                    for suite_name in batch["expectation_suite_names"]:
                        suite = context.get_expectation_suite(suite_name)
                        batch = context.get_batch(batch_kwargs, suite)
                        assets_to_validate.append(batch)
                validation_operator = ge_checkpoint["validation_operator_name"]
            else:
                assets_to_validate.append(
                    context.get_batch(batch_kwargs, expectation_suite_name)
                )

        # Run validation operator
        results = context.run_validation_operator(
            validation_operator,
            assets_to_validate=assets_to_validate,
            run_id={"run_name": run_name or prefect.context.get("task_slug")},
            evaluation_parameters=evaluation_parameters,
        )

        # Generate artifact markdown
        if not disable_markdown_artifact:
            run_info_at_end = True
            validation_results_page_renderer = (
                ge.render.renderer.ValidationResultsPageRenderer(
                    run_info_at_end=run_info_at_end
                )
            )
            rendered_document_content_list = (
                validation_results_page_renderer.render_validation_operator_result(
                    validation_operator_result=results
                )
            )
            markdown_artifact = " ".join(
                ge.render.view.DefaultMarkdownPageView().render(
                    rendered_document_content_list
                )
            )

            create_markdown_artifact(markdown_artifact)

        if results.success is False:
            raise signals.FAIL(result=results)

        return results
