/**
 * Team Responsible : SMART
 * Jira : TORF-467794
 * RHQ CLI script to create a user with read-only rights
 */

var searchCriteria = new SubjectCriteria();
searchCriteria.addFilterFirstName("Username");
var subjectAlreadyExists = (SubjectManager.findSubjectsByCriteria(
		searchCriteria).size() > 0);

pretty.print("Creating subject 'Username'");
if (!subjectAlreadyExists) {
	// create the new user entry
	var newSubject = new Subject();
	newSubject.setEmailAddress('Username@esm.com');
	newSubject.setFirstName('Username');
	newSubject.setLastName('Username');
	newSubject.setFactive(true);
	newSubject.setFsystem(false);
	newSubject.setName('Username');
	var s = SubjectManager.createSubject(newSubject);

	// create the login principal for the user
	SubjectManager.createPrincipal(s.name, 'ericssonadmin');

	// search for the role and create an array
	var c = new RoleCriteria();
	c.addFilterName('Super User Role');
	var roles = RoleManager.findRolesByCriteria(c);
	var role = roles.get(0);
	var rolesArray = new Array(1);
	rolesArray[0] = role.getId();

	// add the new user to the roles in the array
	RoleManager.addRolesToSubject(s.getId(), rolesArray);

	// limit the UI elements visible to the read-only user
	var subject = SubjectManager.login("Username", "ericssonadmin");
	subject.userConfiguration = new Configuration();
	subject = SubjectManager.updateSubject(subject);
	var d = subject.userConfiguration;
	var p = new PropertySimple();
	p.booleanValue = false;
	p.stringValue = "1|1|1|1|1|1|1|1";
	p.name = ".ui.showSubsystems";
	d.put(p);
	subject = SubjectManager.updateSubject(subject);
	pretty.print("Subject 'Username' has been created");
} else {
	pretty.print("Subject 'Username' already exists, skipping creation");
}