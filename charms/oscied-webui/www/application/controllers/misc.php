<?php if ( ! defined('BASEPATH')) exit('No direct script access allowed');

class Misc extends MY_Controller
{
   public function index() {
      $this->add_content('page_title', 'OSCIED - Home');
      $this->add_view('main', 'homepage');

      $header_data['page'] = 'home';
      $this->render($header_data);
   }
   
   public function contact() {
      $this->add_content('page_title', 'OSCIED - Contact Us');
      $this->add_view('main', 'contact');

      $header_data['page'] = 'contact';
      $this->render($header_data);
   }

   private function json_fetch() {
       $this->load->helper('number');
       $this->load->spark('restclient/2.1.0');
       $this->load->library('rest');
       $this->rest->initialize(
               array(
                   'server' => $this->config->item('orchestra_api_url'), 'http_auth' => 'basic',
                   'http_user' => $this->user->mail(), 'http_pass' => $this->user->secret()
                   )
               );
       $response = $this->rest->get('media');
       if ($response->status != 200) {
           print_r($response->value);
           exit;
       }
       return $response->value;
   }

   public function json_encoders() {
       $medias = $this->json_fetch();

       $encoders = array();
       foreach ($medias as $media) {
           if (!isset($media->metadata->measures)) continue;
           $enco = $media->metadata->measures->git_url;
           $encoders[$enco] = 1;
       }

       $out_array = array_keys($encoders);
       $this->output
           ->set_content_type('application/json')
           ->set_output(json_encode($out_array));
   }

   public function json_samplers() {
       $medias = $this->json_fetch();

       $samplers = array();
       foreach ($medias as $media) {
           if ($media->parent != NULL) continue; // only root medias
           $fname = $media->filename;
           $samplers[$fname] = 1;
       }

       $out_array = array_keys($samplers);
       $this->output
           ->set_content_type('application/json')
           ->set_output(json_encode($out_array));
   }

   public function json() {
       $medias = $this->json_fetch();

       // conditions (supported metrics)
       $fmetric = strtolower(@$_GET['metric']);
       if (!in_array($fmetric, array('psnr', 'ssim'))) {
           http_response_code(400);
           die('ERROR: missing/invalid metric!');
       }

       $out_array = array();
       foreach ($medias as $media) {
           // if the media is a root ignore
           if ($media->parent == NULL) continue;
           // if the media has no measures, skip it
           if (!isset($media->metadata->measures)) continue;
           // filter not ready
           if (@$media->status != "READY") continue;

           // filters (all optional)
           if (isset($_GET['date_from'])
               && $media->metadata->add_date < $_GET['date_from']) continue;
           if (isset($_GET['date_to'])
               && $media->metadata->add_date > $_GET['date_to']) continue;
           if (isset($_GET['source'])
               && $media->parent->filename !== $_GET['source']) continue;
           if (isset($_GET['git_url'])
               && $media->measures->git_url !== $_GET['git_url']) continue;

           // value (supported metrics)
           $fmetric_value = $fmetric == 'psnr'
               ? @$media->metadata->measures->psnr
               : @$media->metadata->measures->ssim;

           // output filtered medias list
           $out_array[] = array(
                "git_url" => @$media->metadata->measures->git_url,
                "source" => @$media->parent->filename,
                "filename" => @$media->filename,
                "url" => site_url("media/force_download/". @$media->_id),
                "date" => @$media->metadata->add_date,
                "metric" => $fmetric,
                "value" => $fmetric_value,
                "bitrate" => @$media->metadata->measures->bitrate,
                "git_commit" => @$media->metadata->measures->git_commit,
           );
       }
       $this->output
           ->set_content_type('application/json')
           ->set_output(json_encode($out_array));
   }
}

/* End of file misc.php */
/* Location: ./application/controllers/misc.php */
