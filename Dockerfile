# This assumes that the pytest image has already been made
#   as required for the DCTStack/DataServants
FROM pytest

USER lig:lig
RUN mkdir /home/lig/logs && mkdir /home/lig/conf

WORKDIR /home/lig/Codes/
COPY --chown=lig:lig . MrFreeze/
WORKDIR /home/lig/Codes/MrFreeze

CMD ["python Nora.py"]
