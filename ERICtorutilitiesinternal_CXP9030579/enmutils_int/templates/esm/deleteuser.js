/**
 * Team Responsible : SMART
 * Jira : TORF-467794
 * RHQ CLI script to delete a user with read-only rights
 */

var searchCriteria = new SubjectCriteria();
searchCriteria.addFilterFirstName("Username");
var subjects = SubjectManager.findSubjectsByCriteria(searchCriteria);
var id=subjects.get(0).id;
var ids=[id];
SubjectManager.deleteSubjects(ids);