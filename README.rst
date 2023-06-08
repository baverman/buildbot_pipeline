Buildbot Pipeline
=================

Buildbot Pipeline is a missing piece to make Buildbot (an excellent CI
framework) usable for mere mortals.

* Define steps in VCS using YAML.
* Scripted includes allow to use favorite language to define dynamic steps and
  bring more flexibility than build matrix.
* Trigger filters. Automatic trigger if step file is changed.
* Parallel steps.
* Ability to skip already passed jobs for same commit (can be helpful to rerun flaky tests).
* Fixed concurrency. You can run multiple builds of the same job on single
  worker.
* Native support for JUnit (XUnit) XML reports.
* Artifacts storage on leader node.
* Artifacts and test reports are attached to step. You can easily find cause of
  failure in UI.
* Gerrit integration:

  * Buildbot pipeline tracks all builds started from the same commit and sets
    `Verify` label based on all succeeded jobs.
  * You can rebuild one of failed jobs from buildset and `Verify` would
    be correctly updated.
  * Do not trigger build for WIP patches.


Example:

.. code-block:: yaml

   # buildbot/unit-tests.yaml

   filter:
     files:
       - app/*
       - unit-tests/*

   steps:
     - name: prepare
       shell-fail: pip install -r requirements.txt

     - name: test
       shell: python -m pytest --junitxml=junit.xml --cov-report html:htmlcov unit-tests
       junit: junit.xml
       upload:
         label: coverage report
         src: htmlcov
         link: htmlcov/


Environment variables
---------------------

* `BUILD_ID`: id of a root job, it's uniq accross a build job
* `WORKSPACE`: path to a shared storage for a buid job. Can be used for caches,
  node_modules, virtual environments and so on.
* `BUILD_STATUS`: status of a current build so far. `Codes <https://docs.buildbot.net/latest/developer/results.html>`_.

STDOUT markup
-------------

Buildbot pipeline supports special stdout markup to enrich builds with custom
information.

* `__PIPELINE_LINK__ name url`: adds a user provided link to a current step.
* `__PIPELINE_PROP__ name value`: adds a user provided property to a current build.
  You can access property value in following steps.

For example:

.. code-block:: yaml

   steps:
     - name: test
       shell: |
           build_id=$(build-package.sh)
           echo __PIPELINE_LINK__ artifacts http://build.corp.com/artifacts/$build_id
