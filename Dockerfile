# This assumes that the ligbase image has already been made
#   as required for the DCTStack/DataServants
FROM ligbase

USER lig:lig
WORKDIR /home/lig/Codes/
COPY --chown=lig:lig . MrFreeze/
WORKDIR /home/lig/Codes/MrFreeze

CMD ["python Nora.py"]
