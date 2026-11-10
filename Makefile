.PHONY: test test-pr-workflows test-ansible lint

test: test-pr-workflows test-ansible

test-pr-workflows:
	python3 -m unittest discover -s tests -p 'test_pr_workflow.py' -v

test-ansible:
	ANSIBLE_ROLES_PATH=.. ansible-playbook -i tests/inventory tests/test.yml

lint:
	ruff check --select E4,E7,E9,F,I files/scripts/pr_workflow.py tests/test_pr_workflow.py
	ruff format --check files/scripts/pr_workflow.py tests/test_pr_workflow.py
	yamllint defaults tasks tests vars
	ANSIBLE_ROLES_PATH=.. ansible-playbook -i tests/inventory tests/test.yml --syntax-check
