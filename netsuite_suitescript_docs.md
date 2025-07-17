# N/action Module Script Samples

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_0302035713.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
N/action Module Script Samples
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
N/action Module Script Samples
The following script samples demonstrate how to use the features of the N/action module:
Important
The samples included in this section are intended to show how actions work in SuiteScript at a high-level. For specific samples, see
Supported Record Actions
.
Locate and Execute an Action on a Timebill Record
Find Actions Available for the Timebill Record Asynchronously Using Promise Methods
Execute a Bulk Action on a Timebill Record
Locate and Execute an Action on a Timebill Record
The following sample finds and executes an action on the timebill record without promises.
Note
This sample script uses the
require
function so that you can copy it into the SuiteScript Debugger and test it. You must use the
define
function in an entry point script (the script you attach to a script record and deploy). For more information, see
SuiteScript 2.x Script Basics
and
SuiteScript 2.x Script Types
.
/**
 * @NApiVersion 2.x
 */
require
(
[
'N/action'
,
'N/record'
]
,
function
(
action
,
record
)
{
// create timebill record
var
rec
=
record
.
create
(
{
type
:
'timebill'
,
isDynamic
:
true
}
)
;
rec
.
setValue
(
{
fieldId
:
'employee'
,
value
:
104
}
)
;
rec
.
setValue
(
{
fieldId
:
'location'
,
value
:
312
}
)
;
rec
.
setValue
(
{
fieldId
:
'hours'
,
value
:
5
}
)
;
var
recordId
=
rec
.
save
(
)
;
var
actions
=
action
.
find
(
{
recordType
:
'timebill'
,
recordId
:
recordId
}
)
;
log
.
debug
(
"We've got the following actions: "
+
Object
.
keys
(
actions
)
)
;
if
(
actions
.
approve
)
{
var
result
=
actions
.
approve
(
)
;
log
.
debug
(
"Timebill has been successfully approved"
)
;
}
else
{
log
.
debug
(
"The timebill is already approved"
)
;
}
}
)
;
// Outputs the following:
// We've got the following actions: approve, reject
// Timebill has been successfully approved
Copy
Find Actions Available for the Timebill Record Asynchronously Using Promise Methods
The following sample asynchronously finds actions available for a timebill record and then executes one with promises.
Note
This sample script uses the
require
function so that you can copy it into the SuiteScript Debugger and test it. You must use the
define
function in an entry point script (the script you attach to a script record and deploy). For more information, see
SuiteScript 2.x Script Basics
and
SuiteScript 2.x Script Types
.
/**
 * @NApiVersion 2.x
 * @NScriptType ClientScript
 */
require
(
[
'N/action'
,
'N/record'
]
,
function
(
action
,
record
)
{
// create timebill record
var
rec
=
record
.
create
(
{
type
:
'timebill'
,
isDynamic
:
true
}
)
;
rec
.
setValue
(
{
fieldId
:
'employee'
,
value
:
104
}
)
;
rec
.
setValue
(
{
fieldId
:
'location'
,
value
:
312
}
)
;
rec
.
setValue
(
{
fieldId
:
'hours'
,
value
:
5
}
)
;
var
recordId
=
rec
.
save
(
)
;
// find all qualified actions and then execute approve if available
action
.
find
.
promise
(
{
recordType
:
'timebill'
,
recordId
:
recordId
}
)
.
then
(
function
(
actions
)
{
console
.
log
(
"We've got the following actions: "
+
Object
.
keys
(
actions
)
)
;
if
(
actions
.
approve
)
{
actions
.
approve
.
promise
(
)
.
then
(
function
(
result
)
{
console
.
log
(
"Timebill has been successfully approved"
)
;
}
)
;
}
else
{
console
.
log
(
"The timebill is already approved"
)
;
}
}
)
;
}
)
;
// Outputs the following:
// We've got the following actions:
// The timebill has been successfully approved
Copy
Execute a Bulk Action on a Timebill Record
The following sample shows how to execute a bulk approve action on a timebill record using different parameters.
Note
This sample script uses the
require
function so that you can copy it into the SuiteScript Debugger and test it. You must use the
define
function in an entry point script (the script you attach to a script record and deploy). For more information, see
SuiteScript 2.x Script Basics
and
SuiteScript 2.x Script Types
.
Important
The following code samples do not serve as an order of execution,
getBulkStatus
should be executed later on and not right after the execution of
action.executeBulk()
.
/**
 * @NApiVersion 2.x
 */
require
(
[
'N/action'
,
'N/util'
]
function
(
action
,
util
)
{
// 1a) Bulk execute the specified action on a provided list of record IDs.
// The params property is an array of parameter objects where each object contains required recordId and arbitrary additional parameters.
var
handle
=
action
.
executeBulk
(
{
recordType
:
"timebill"
,
id
:
"approve"
,
params
:
[
{
recordId
:
1
,
note
:
"this is a note for 1"
}
,
{
recordId
:
5
,
note
:
"this is a note for 5"
}
,
{
recordId
:
23
,
note
:
"this is a note for 23"
}
]
}
)
}
)
;
// 1b) Bulk execute the specified action on a provided list of record IDs.
// The parameters in the previous sample are similar and can be generated programatically using the map function.
var
searchResults
=
/* result of a search, for example, [1, 5, 23] */
;
var
handle
=
action
.
executeBulk
(
{
recordType
:
"timebill"
,
id
:
"approve"
,
params
:
searchResults
.
map
(
function
(
v
)
{
return
{
recordId
:
v
,
note
:
"this is a note for "
+
v
}
;
}
)
}
)
;
// 2a) Bulk execute the specified action on a provided list of record IDs.
// This time with homogenous parameters, that is, all parameter objects are equal except recordId.
var
handle
=
action
.
executeBulk
(
{
recordType
:
"timebill"
,
id
:
"approve"
,
params
:
searchResults
.
map
(
function
(
v
)
{
return
{
recordId
:
v
,
foo
:
"bar"
,
name
:
"John Doe"
}
;
}
)
}
)
;
// 2b) Bulk execute the specified action on a provided list of record IDs.
// This time with homogenous parameters. Equivalent to the previous sample.
var
commonParams
=
{
foo
:
"bar"
,
name
:
"John Doe"
}
;
var
handle
=
action
.
executeBulk
(
{
recordType
:
"timebill"
,
id
:
"approve"
,
params
:
searchResults
.
map
(
function
(
v
)
{
return
util
.
extend
(
{
recordId
:
v
}
,
commonParams
)
;
}
)
}
)
;
// 3) Bulk execute the specified action on a provided list of record IDs.
// This is the simplest usage with no extra parameters besides the record ID.
var
handle
=
action
.
executeBulk
(
{
recordType
:
"timebill"
,
id
:
"approve"
,
params
:
searchResults
.
map
(
function
(
v
)
{
return
{
recordId
:
v
}
}
)
}
)
;
// 4) Bulk execute the specified action on all record instances that qualify.
// Since we don't have a list of recordIds in hand, we only provide the callback
// that will later be used to transform a recordId to the corresponding parameters object.
var
handle
=
action
.
executeBulk
(
{
recordType
:
"timebill"
,
id
:
"approve"
,
condition
:
action
.
ALL_QUALIFIED_INSTANCES
,
paramCallback
:
function
(
v
)
{
return
{
recordId
:
v
,
note
:
"this is a note for "
+
v
}
;
}
}
)
;
// 5) Get a particular action for a particular record type.
var
approveTimebill
=
action
.
get
(
{
recordType
:
"timebill"
,
id
:
"approve"
}
)
;
// 6) Bulk execute the previously obtained action on a provided list of record IDs.
// Params are generated the same way as above in action.executeBulk().
var
handle
=
approveTimebill
.
executeBulk
(
{
params
:
searchResults
.
map
(
function
(
v
)
{
return
{
recordId
:
v
,
note
:
"this is a note for "
+
v
}
;
}
)
}
)
;
// 7) Bulk execute the previously obtained action on all record instances that qualify.
var
handle
=
approveTimebill
.
executeBulk
(
{
condition
:
action
.
ALL_QUALIFIED_INSTANCES
,
paramCallback
:
function
(
v
)
{
return
{
recordId
:
v
,
note
:
"this is a note for "
+
v
}
;
}
}
)
;
// 8) Get status of a bulk action execution.
var
res
=
action
.
getBulkStatus
(
{
taskId
:
handle
}
)
;
// returns a RecordActionTaskStatus object
log
.
debug
(
res
.
status
)
;
}
)
;
Copy
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.execute(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1509391388.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.execute(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.execute(options)
Method Description
Executes the record action and returns the action results in a plain JavaScript object.
If the action fails, it is listed in the results object’s
notifications
property. If the action executes successfully, the
notifications
property is usually empty.
Returns
Object
Supported Script Types
Client and server scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2018.2
Parameters
Note
The
options
parameter is a JavaScript object.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.id
string
required
The action ID.
For a list of action IDs, see
Supported Record Actions
.
options.params
Object
required
Action arguments.
options.params.recordId
int
required
The record instance ID.
This is the NetSuite record internal ID.
Errors
Error Code
Thrown If
RECORD_DOES_NOT_EXIST
The specified record instance does not exist.
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
A required parameter is missing.
Syntax
Important
The following code snippet shows the syntax for this member. It is not a functional example. For a complete script example, see
N/action Module Script Samples
and
Revenue Arrangement Record Actions
.
// Add additional code
...
var
myResult
=
action
.
execute
(
{
id
:
'note'
,
recordType
:
'timebill'
,
params
:
{
recordId
:
1
}
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.execute.promise(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1509392030.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.execute.promise(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.execute.promise(options)
Method Description
Executes the record action asynchronously.
If the action fails, it is listed in the results object’s
notifications
property. If the action executes successfully, the
notifications
property is usually empty.
Note
The parameters and errors thrown for this method are the same as those for
action.execute(options)
. For more information about promises, see
Promise Object
.
Returns
Promise Object
Synchronous Version
action.execute(options)
Supported Script Types
Client scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2018.2
Parameters
Note
The
options
parameter is a JavaScript object.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.id
string
required
The action ID.
For a list of action IDs, see
Supported Record Actions
.
options.params
Object
required
Action arguments.
options.params.recordId
string
required
The record instance ID.
This is the NetSuite record internal ID.
Errors
Error Code
Thrown If
RECORD_DOES_NOT_EXIST
The specified record instance does not exist.
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
A required parameter is missing.
Syntax
Important
The following code sample shows the syntax for this member. It is not a functional example. For a complete promise script example, see
Promise Object
.
// Add additional code
...
action
.
execute
.
promise
(
{
id
:
'note'
,
recordType
:
'timebill'
,
params
:
{
recordId
:
1
}
}
)
.
then
(
function
(
result
)
{
// Process the result
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.executeBulk(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1540815927.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.executeBulk(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.executeBulk(options)
Method Description
Executes an asynchronous bulk record action and returns its task ID for status queries with
action.getBulkStatus(options)
. The
options.params
parameter is mutually exclusive to
options.condition
and
options.paramCallback
.
Returns
string
Supported Script Types
Client and server scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
50 units
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2019.1
Parameters
Note
The options parameter is a JavaScript object. The
options.params
array consists of parameter objects. The values that are required in each parameter object vary for action types. The only value that is always required is
recordId
.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.id
string
required
The action ID.
options.params
array
required
An array of parameter objects. Each object corresponds to one record ID of the record for which the action is to be executed. The object has the following form:
{
recordId
:
1
,
someParam
:
'example1'
,
otherParam
:
'example2'
}
Copy
The
recordId
parameter is always required, other parameters are optional and are specific to the particular action.
options.condition
string
optional
The condition used to select record IDs of records for which the action is to be executed. Only the action.ALL_QUALIFIED_INSTANCES constant is currently supported.
The action.ALL_QUALIFIED_INSTANCES condition only works correctly if the author of the record action has implemented the
findInstances
method of the
RecordActionQualifier
interface. An example of such action is
approve
on the timebill and timesheet records.
options.paramCallback
string
optional
Function that takes record ID and returns the parameter object for the specified record ID.
Errors
Error Code
Thrown If
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
The
options.recordType
parameter is missing or undefined.
Syntax
Important
The following code snippet shows the syntax for this member. It is not a functional example. For a complete script example, see
N/action Module Script Samples
.
// Add additional code
...
var
handle
=
action
.
executeBulk
(
{
recordType
:
'timebill'
,
id
:
'approve'
,
params
:
[
{
recordId
:
1
,
note
:
'this is a note for 1'
}
,
{
recordId
:
5
,
note
:
'this is a note for 5'
}
,
{
recordId
:
23
,
note
:
'this is a note for 23'
}
]
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.find(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1509389605.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.find(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.find(options)
Method Description
Performs a search for available record actions. If only the
recordType
parameter is specified, all actions available for the record type are returned. If the
recordId
parameter is also specified, then only actions that qualify for execution on the given record instance are returned. If the
id
parameter is specified, then only the action with the specified action ID is returned.
This method returns a plain JavaScript object of NetSuite record actions available for the record type. The object contains one or more
action.Action
objects. If there are no available actions for the specified record type, an empty object is returned.
If the
recordId
is specified in this call, the actions that are found are considered qualified. You do not have to provide the
recordId
to execute a qualified action.
Returns
Object
Supported Script Types
Client and server scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2018.2
Parameters
Note
The
options
parameter is a JavaScript object.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.recordId
string
optional
The record instance ID.
options.id
string
optional
The action ID.
Errors
Error Code
Thrown If
RECORD_DOES_NOT_EXIST
The specified record ID does not exist.
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
The
options.recordType
parameter is missing or undefined.
Syntax
Important
The following code snippet shows the syntax for this member. It is not a functional example. For a complete script example, see
N/action Module Script Samples
.
// Add additional code
...
var
actions
=
action
.
find
(
{
recordType
:
'timebill'
,
recordId
:
recordId
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.find.promise(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1509391246.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.find.promise(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.find.promise(options)
Method Description
Performs a search for available record actions asynchronously. If only the
recordType
parameter is specified, all actions available for the record type are returned. If the
recordId
parameter is also specified, then only actions that qualify for execution on the given record instance are returned. If the
id
parameter is specified, the only the action with the specified action ID is returned.
This method returns a plain JavaScript object of NetSuite record actions available for the record type. The object contains one or more
action.Action
objects. If there are no available actions for the specified record type, an empty object is returned.
If the
recordId
is specified in this call, the actions that are found are considered qualified. You do not have to provide the
recordId
to execute a qualified action.
Note
The parameters and errors thrown for this method are the same as those for
action.find(options)
. For more information about promises, see
Promise Object
.
Returns
Promise Object
Synchronous Version
action.find(options)
Supported Script Types
Client scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2018.2
Parameters
Note
The
options
parameter is a JavaScript object.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.recordId
string
optional
The record instance ID.
options.id
string
optional
The action ID.
Errors
Error Code
Thrown If
RECORD_DOES_NOT_EXIST
The specified record ID does not exist.
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
The
options.recordType
parameter is missing or undefined.
Syntax
Important
The following code sample shows the syntax for this member. It is not a functional example. For a complete promise script example, see
Promise Object
.
// Add additional code
...
var
promise
=
action
.
find
.
promise
(
{
recordType
:
'timebill'
}
)
;
promise
.
then
(
function
(
actionList
)
{
// Process the list of actions
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.get(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1509384818.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.get(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.get(options)
Method Description
Returns an executable record action for the specified record type. If the
recordId
parameter is specified, the action object is returned only if the specified action can be executed on the specified record instance.
Returns
action.Action
Supported Script Types
Client and server scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2018.2
Parameters
Note
The
options
parameter is a JavaScript object.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.recordId
string
optional
The record instance ID.
options.id
string
required
The ID of the action.
For a list of action IDs, see
Supported Record Actions
.
Errors
Error Code
Thrown If
RECORD_DOES_NOT_EXIST
The specified record instance does not exist.
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
A required parameter is missing.
Syntax
Important
The following code snippet shows the syntax for this member. It is not a functional example. For a complete script example, see
N/action Module Script Samples
.
// Add additional code
...
var
myAction
=
action
.
get
(
{
recordType
:
'timebill'
,
id
:
'approve'
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.get.promise(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1509385970.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.get.promise(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.get.promise(options)
Method Description
Returns an executable record action for the specified record type asynchronously. If the
recordId
parameter is specified, the action object is returned only if the specified action can be executed on the specified record instance.
Note
The parameters and errors thrown for this method are the same as those for
action.get(options)
. For more information about promises, see
Promise Object
.
Returns
Promise Object
Synchronous Version
action.get(options)
Supported Script Types
Client scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2018.2
Parameters
Note
The
options
parameter is a JavaScript object.
Parameter
Type
Required / Optional
Description
options.recordType
string
required
The record type.
For a list of record types, see
record.Type
.
options.recordId
string
optional
The record instance ID.
options.id
string
required
The ID of the action.
For a list of action IDs, see
Supported Record Actions
.
Errors
Error Code
Thrown If
RECORD_DOES_NOT_EXIST
The specified record instance does not exist.
SSS_INVALID_ACTION_ID
The specified action does not exist on the specified record type.
– or –
The action exists, but cannot be executed on the specified record instance.
SSS_INVALID_RECORD_TYPE
The specified record type is invalid.
SSS_MISSING_REQD_ARGUMENT
A required parameter is missing.
Syntax
Important
The following code sample shows the syntax for this member. It is not a functional example. For a complete promise script example, see
Promise Object
.
// Add additional code
...
action
.
get
.
promise
(
{
recordType
:
'timebill'
,
id
:
'approve'
}
)
.
then
(
function
(
action
)
{
// Process the action object
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

# action.getBulkStatus(options)

**Source URL:** <https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl?fid=section_1540816132.html>

SuiteCloud Platform
SuiteScript
SuiteScript 2.x API Reference
SuiteScript 2.x Modules
N/action Module
action.getBulkStatus(options)
Applies to
SuiteScript 2.x | APIs | SuiteCloud Developer
action.getBulkStatus(options)
Method Description
Returns the current status of
action.executeBulk(options)
for the specified task ID. The bulk execution status is returned in a status object.
Returns
RecordActionTaskStatus Object Members
Supported Script Types
Client and server scripts
For more information, see
SuiteScript 2.x Script Types
.
Governance
None
Module
N/action Module
Sibling Object Members
N/action Module Members
Since
2019.1
Parameters
Parameter
Type
Required / Optional
Description
options.taskId
string
required
The task ID returned by a previous
action.executeBulk(options)
call.
Syntax
Important
The following code snippet shows the syntax for this member. It is not a functional example. For a complete script example, see
N/action Module Script Samples
.
// Add additional code
...
// Obtain the status as a RecordActionTaskStatus object
var
res
=
action
.
getBulkStatus
(
{
taskId
:
handle
}
)
;
...
// Add additional code
Copy
Related Topics
N/action Module
SuiteScript 2.x Modules
SuiteScript 2.x
General Notices
Copyright ©  2005, 2025, Oracle and/or its affiliates. All rights reserved.
How helpful was this topic?
Five Stars
Four Stars
Three Stars
Two Stars
One Star

---

