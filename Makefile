MAP ?= maps/maps/challenger/01_the_impossible_dream.txt

install:
	pip install flake8 mypy

run:
	python3 main.py $(MAP)

debug:
	python3 -m pdb main.py $(MAP)

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	flake8 main.py parser.py simulation.py models.py
	mypy main.py parser.py simulation.py models.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
