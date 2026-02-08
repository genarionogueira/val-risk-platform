.PHONY: help demo test up

help:
	@echo "Pricing project - available targets:"
	@echo ""
	@echo "  make help   - print this help"
	@echo "  make demo   - run pricing-library demo (ZCB, swap, FX forward, mortgage)"
	@echo "  make test   - run pricing-library test suite (pytest)"
	@echo "  make up     - start API and Jupyter via docker-compose"
	@echo ""

demo:
	cd pricing-library && poetry run python -m pricing.demo

test:
	cd pricing-library && poetry run pytest -q

up:
	docker-compose up --build
