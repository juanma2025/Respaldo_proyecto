#Stage 1:Build Frontend
From node:18 as build-stage

WORKDIR /code

COPY ./Front_Citas_Medicas/ /code/Front_Citas_Medicas/

WORKDIR /code/Front_Citas_Medicas

RUN npm install

RUN npm run build

#Stage 2:Build Backend
FROM python:3:11:0

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY .GestionCitasMedicas/ /code/GestionCitasMedicas/

RUN pip install -r ./GestionCitasMedicas/requirements.txt

COPY --from=build-stage ./code/Front_Citas_Medicas/build /code/GestionCitasMedicas/static/
COPY --from=build-stage ./code/Front_Citas_Medicas/build/static /code/GestionCitasMedicas/static/
COPY --from=build-stage ./code/Front_Citas_Medicas/build/index.html /code/GestionCitasMedicas/templates/index.html

RUN python ./GestionCitasMedicas/manage.py migrate

RUN python ./GestionCitasMedicas/manage.py collectstatic --no-input

EXPOSE 80

WORKDIR /code/GestionCitasMedicas

cmd ["guinicorn", "GestionCitasMedicas.wsgi.application","--bind", "0.0.0.0:8000"]