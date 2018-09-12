CC = erlc
DO = erl -noshell

.PHONY: erlang
erlang: clean projects

projects: projects.beam
	$(DO) -s $@ start -s init stop

projects.beam: projects.erl
	$(CC) $^

.PHONY : clean
clean: 
	rm -rf *.dump *.beam

