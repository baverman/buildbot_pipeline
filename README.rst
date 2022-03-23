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
