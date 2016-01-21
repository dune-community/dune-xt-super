#assumes global $OPTS
function getOptsFile( )
{
if [ x${1} = x ] ; then
  OPTS=config.opts.wwu_no_documentation
  ln -sf ${OPTS} config.opts.last
else
	OPTS=${1}
	ln -sf ${OPTS} config.opts.last
fi
}

if  [ $(ionice -c 3 /bin/true) ] ; then
  IONICE="ionice -c 3"
else
  IONICE=""
fi

if [ $(type -t sd) ] ; then
  CMD="sd ${IONICE} nice time ./dune-common/bin/dunecontrol"
else
  CMD="${IONICE} nice time ./dune-common/bin/dunecontrol"
fi
