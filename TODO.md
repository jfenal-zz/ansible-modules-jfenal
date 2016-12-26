
redhat_repositories TODO list
=============================

- mode=idempotent:
  - id=* state=disabled: easy, already done, does not need to query the actual list of repos

  - id=list,of,repos state=enabled
    Needs to worked out, since we have to
    1. query current list of repos (1st fork to subscription-manage repos --list)
    2. check which are enabled or disabled, build command line
    3. issue a second command to enable missing repos (2nd potential fork to
       subscription-manage repos --enable=list,repos) and disable repos not listed
       (3rd potential fork to subscription-manage repos --disable=list,repos
    4. return list of enabled and disabled repos
       repos['enabled'] : list of enabled repos
       repos['disabled'] : list of disabled repos
    5. Optional: request new list of repos and check to possibly return error on non
       enabled/disabled repo

  - id=list,of,repos state=disabled: same as above, only reversed

- Add mode=incremental and just enable or disable requested repos, should be
  faster than above (fire&forget mode)


