# Cash Application Automation: Teams flow, pending file and alerts (build detail)

Moved out of the PRD (Appendix A) on 2026-11-13. The PRD keeps the decisions in sections 7.7 and 7.8. This file is for whoever builds and supports the flow. Every statement here is **future state, proposed**: nothing in it is built yet. The flow waits on the Power Automate flow being created (owner to confirm with Jack Ehlers). Every number here is a starting point and can be changed.

## 1. Teams notification flow and the pending file

- **Workbook open (future state, proposed).** The tool writes to Walter's workbook only when it is closed. If it is open, the tool adds a row to a SharePoint list with the status "file open", and a Power Automate flow posts a Teams message to Walter and Joshua asking Walter to close it. The tool tries again every 10 minutes. When the write works, the tool adds a "done" row and the flow tells Walter and Joshua. Each row holds the date and time, the status (started, file open, done, gave up or failed) and a short message, so the list is also a record of how often the workbook is open.
- **If it never gets to write (future state, proposed).** After 2 hours the tool stops and adds a "gave up" row. The flow messages Walter, Joshua and Suzan with how many lines were held and how many were flagged as exceptions, and says that the pending file will be copied over on the next day's run. The deposit workbook is separate and is not affected, so Walter can still upload and post that day.
- **The pending file (Transactions-and-Metrics_PENDING).** There is one pending file, saved next to Walter's workbook in Bank > Electronic Transaction Report. It holds the lines of every day that could not be written, with the date on each line. Its presence is the warning: if the file is not there, nothing is pending. The flow also checks for it each morning, so the alert still works if the tool itself fails.
- **Catching up.** On the next run, if Walter's workbook is closed, the tool writes the pending days first, oldest first, and then the new day. The duplicate key (payment date, payer, check or transaction number) means a line is written once even if the tool tries twice. Until the catch-up, the held days' open exceptions are missing from Walter's list and their Daily Metrics rows are late. The tool still flags exceptions in the deposit workbook.
- **After the copy.** The tool first adds the copied lines to one running archive file, _Transactions-and-Metrics_PENDING, in a folder called _pending-archive (next to the pending file), each line with the date it was copied over. It checks that the archive was written, then deletes the pending file. If the archive step fails, the pending file stays and the warning stays on.
- **Backlog limit.** If the pending file is still there after 2 business days, the flow messages Walter, Joshua, Suzan and Delphine. This should never happen, so it is treated as a problem to fix.
- **Status values.** The SharePoint list rows use started, file open, done, gave up or failed. The times used above are 10 minutes between tries, 2 hours before giving up, and 2 business days for the backlog alert.

## 2. Alerts and recovery

- **Alerts.** All alerts go through Teams, using the SharePoint list and the flow. The tool adds a "started" row when it begins and a final row (done, gave up or failed) when it ends. Two checks do not depend on the tool, so they work even if it is dead. The flow alerts Walter, Joshua, Jack and Suzan if there is no "started" row by 12 noon ET (the job did not start), and if there is no final row by 2 PM ET (the job stopped partway). The 2-hour wait for a locked workbook happens after "started", so it does not trigger the noon check. The two times are starting points.
- **Recovery.** Rerunning a date is safe, because a rerun never adds a duplicate. To start a run by hand, a named person adds a "run request" row, with the date, to the same SharePoint list. The flow sees it and starts the job. No password is used; access is by who may add rows: Walter, Joshua, Suzan, Marina and Jack. How the flow reaches the job, and the steps to restore the service account, wait until the AWS server and the service account are set up.

## 3. Teams channel and list changes (future state, proposed)

- **Channel.** One Teams channel, Cash Application Automation (name to confirm). Members at the start: Joshua Barnhill, Suzan Oslin and Delphine Hartsel. More people can be added without changing the tool.
- **What it gets.** One post for each run that changed the lists, with an @mention for the three members. A row someone adds to the Reasons or Dept codes list counts as confirmed; the post lets the team respond if it is wrong.
- **Alerts.** The alerts in sections 1 and 2 (workbook open, gave up, job not started, job stopped partway) go to the same channel, with the same people mentioned. This replaces the separate messages to individuals.
- **How.** The same SharePoint list and flow as the alerts. If the post does not go out, the checks in section 2 still cover a run that did not start or finish.

## 4. Test cases for the flow and support

These are cases 10 to 14 of the PRD test cases (section 8.1 of the PRD holds cases 1 to 9). The go-live gate in PRD section 7.8 requires all 14 to pass.

| No. | Case | What we do | Pass when |
|---|---|---|---|
| 10 | Walter's workbook is open | Open the workbook in Excel and start a run. | The tool writes nothing and adds a "file open" row. Walter and Joshua get a Teams message. After Walter closes the file, the tool writes the sheets and adds a "done" row, and Walter and Joshua get a "done" message. |
| 11 | The workbook stays open for 2 hours | Keep the workbook open past the cutoff. | The tool adds a "gave up" row, and Walter, Joshua and Suzan get a message that says the pending file will be copied over on the next run. The deposit workbook is still produced. On the next run, with the file closed, the pending days are written first and then the new day. The pending file is archived and deleted, and no line is duplicated. |
| 12 | The job does not start, or stops partway | Switch off the schedule for one day, then stop a run partway. | With no "started" row by 12 noon ET, and with no final row by 2 PM ET, the flow sends a Teams alert to Walter, Joshua, Jack and Suzan. |
| 13 | Start a run by hand | Add a "run request" row for a past date. | The job runs for that date and adds no duplicates. This test waits for the AWS server and the service account. |
| 14 | New list rows | Add a reason and a Dept code in the live workbook and run. | The two rows are in the template and one channel post lists them. A second run adds nothing. |
