FROM intel4coro/base-notebook:20.04-noetic

USER ${NB_USER}

COPY --chown=${NB_USER}:users ./ /home/${NB_USER}/llama/

WORKDIR /home/${NB_USER}/llama/

RUN pip3 install -r requirements.txt